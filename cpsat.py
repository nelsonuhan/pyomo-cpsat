import logging
import re
import sys

from pyomo.common.collections import ComponentSet, ComponentMap, Bunch
from pyomo.common.dependencies import attempt_import
from pyomo.common.errors import ApplicationError
from pyomo.common.tempfiles import TempfileManager
from pyomo.common.tee import capture_output
from pyomo.core.expr.numvalue import is_fixed
from pyomo.core.expr.numvalue import value
from pyomo.core.staleflag import StaleFlagManager
from pyomo.repn import StandardRepn, generate_standard_repn
from pyomo.solvers.plugins.solvers.direct_solver import DirectSolver
from pyomo.solvers.plugins.solvers.direct_or_persistent_solver import (
    DirectOrPersistentSolver,
)
from pyomo.core.kernel.objective import minimize, maximize
from pyomo.opt.results.results_ import SolverResults
from pyomo.opt.results.solution import Solution, SolutionStatus
from pyomo.opt.results.solver import TerminationCondition, SolverStatus
from pyomo.opt.base import SolverFactory
from pyomo.core.base.suffix import Suffix
import pyomo.core.base.var

from ortools.sat.python import cp_model

logger = logging.getLogger('pyomo.solvers')


class DegreeError(ValueError):
    pass


@SolverFactory.register('cpsat', doc='Direct Python interface to CP-SAT')
class CpsatDirect(DirectSolver):
    _name = None
    _version = None

    def __init__(self, **kwds):
        kwds['type'] = 'cpsat_direct'
        super(CpsatDirect, self).__init__(**kwds)

        self._python_api_exists = True

        self._max_obj_degree = 1
        self._max_constraint_degree = 1

        # Note: Undefined capabilities default to None
        self._capabilities.linear = True
        self._capabilities.quadratic_objective = False
        self._capabilities.quadratic_constraint = False
        self._capabilities.integer = True
        self._capabilities.sos1 = False
        self._capabilities.sos2 = False

    def available(self, exception_flag=True):
        return True

    def license_is_valid(self):
        return True

    def version(self):
        return (0, 0, 0)

    def _get_expr_from_pyomo_repn(self, repn, max_degree=1):
        referenced_vars = ComponentSet()

        degree = repn.polynomial_degree()
        if (degree is None) or (degree > max_degree):
            raise DegreeError(
                f'CpsatDirect does not support expressions of degree {degree}.'
            )

        if len(repn.linear_vars) > 0:
            referenced_vars.update(repn.linear_vars)
            cpsat_expr = cp_model.LinearExpr.WeightedSum(
                [self._pyomo_var_to_solver_var_map[i] for i in repn.linear_vars],
                repn.linear_coefs
            )
        else:
            cpsat_expr = 0

        cpsat_expr += repn.constant

        return cpsat_expr, referenced_vars

    def _get_expr_from_pyomo_expr(self, expr, max_degree=1):
        repn = generate_standard_repn(expr, quadratic=False)

        try:
            cpsat_expr, referenced_vars = self._get_expr_from_pyomo_repn(repn, max_degree)
        except DegreeError as e:
            msg = e.args[0]
            msg += f'\nexpr: {expr}'
            raise DegreeError(msg)

        return cpsat_expr, referenced_vars

    def _cpsat_bounds_from_var(self, var):
        if var.is_fixed():
            val = var.value
            return val, val

        if var.has_lb():
            lb = value(var.lb)
        else:
            raise ValueError(
                f"Encountered a variable ({var.name}) with no lower bound, "
                "which is invalid for CP-SAT instances."
            )

        if var.has_ub():
            ub = value(var.ub)
        else:
            raise ValueError(
                f"Encountered a variable ({var.name}) with no upper bound, "
                "which is invalid for CP-SAT instances."
            )

        return lb, ub

    def _add_var(self, var):
        # CP-SAT only allows integer variables
        if var.is_continuous():
            raise ValueError(
                "Cannot use continuous variables in CP-SAT."
            )

        varname = self._symbol_map.getSymbol(var, self._labeler)
        # print(varname)
        lb, ub = self._cpsat_bounds_from_var(var)

        cpsat_var = self._solver_model.NewIntVar(lb, ub, varname)

        self._pyomo_var_to_solver_var_map[var] = cpsat_var
        self._solver_var_to_pyomo_var_map[cpsat_var] = var
        self._referenced_variables[var] = 0

    def _set_instance(self, model, kwds={}):
        self._range_constraints = set()
        DirectOrPersistentSolver._set_instance(self, model, kwds)
        self._pyomo_con_to_solver_con_map = dict()
        self._solver_con_to_pyomo_con_map = ComponentMap()
        self._pyomo_var_to_solver_var_map = ComponentMap()
        self._solver_var_to_pyomo_var_map = ComponentMap()
        self._solver_model = cp_model.CpModel()
        self._solver_solver = cp_model.CpSolver()
        self._solver_status = None

        self._add_block(model)

        for var, n_ref in self._referenced_variables.items():
            if n_ref != 0:
                if var.fixed:
                    if not self._output_fixed_variable_bounds:
                        raise ValueError(
                            "Encountered a fixed variable (%s) inside "
                            "an active objective or constraint "
                            "expression on model %s, which is usually "
                            "indicative of a preprocessing error. Use "
                            "the IO-option 'output_fixed_variable_bounds=True' "
                            "to suppress this error and fix the variable "
                            "by overwriting its bounds in the CP-SAT instance."
                            % (var.name, self._pyomo_model.name)
                        )

    def _add_block(self, block):
        DirectOrPersistentSolver._add_block(self, block)

    def _add_constraint(self, con):
        if not con.active:
            return None

        if is_fixed(con.body):
            if self._skip_trivial_constraints:
                return None

        conname = self._symbol_map.getSymbol(con, self._labeler)

        if con._linear_canonical_form:
            cpsat_expr, referenced_vars = self._get_expr_from_pyomo_repn(
                con.canonical_form(), self._max_constraint_degree
            )
        else:
            cpsat_expr, referenced_vars = self._get_expr_from_pyomo_expr(
                con.body, self._max_constraint_degree
            )

        if con.has_lb():
            if not is_fixed(con.lower):
                raise ValueError(
                    f"Lower bound of constraint {con} is not constant."
                )

        if con.has_ub():
            if not is_fixed(con.upper):
                raise ValueError(
                    f"Upper bound of constraint {con} is not constant."
                )

        if con.equality:
            cpsat_lb = int(value(con.lower))
            cpsat_ub = int(value(con.lower))
        elif con.has_lb() and con.has_ub():
            cpsat_lb = int(value(con.lower))
            cpsat_ub = int(value(con.upper))
        elif con.has_lb():
            cpsat_lb = int(value(con.lower))
            cpsat_ub = cp_model.INT_MAX
        elif con.has_ub():
            cpsat_lb = cp_model.INT_MIN
            cpsat_ub = int(value(con.upper))
        else:
            raise ValueError(
                "Constraint does not have a lower "
                "or an upper bound: {0} \n".format(con)
            )

        cpsat_con = self._solver_model.AddLinearConstraint(
            cpsat_expr, cpsat_lb, cpsat_ub
        )
        cpsat_con_proto = cpsat_con.Proto()
        cpsat_con_proto.name = conname

        for var in referenced_vars:
            self._referenced_variables[var] += 1
        self._vars_referenced_by_con[con] = referenced_vars
        self._pyomo_con_to_solver_con_map[con] = cpsat_con
        self._solver_con_to_pyomo_con_map[cpsat_con] = con

    def _set_objective(self, obj):
        if self._objective is not None:
            for var in self._vars_referenced_by_obj:
                self._referenced_variables[var] -= 1
            self._vars_referenced_by_obj = ComponentSet()
            self._objective = None

        if obj.active is False:
            raise ValueError('Cannot add inactive objective to solver.')

        cpsat_expr, referenced_vars = self._get_expr_from_pyomo_expr(
            obj.expr, self._max_obj_degree
        )

        for var in referenced_vars:
            self._referenced_variables[var] += 1

        if obj.sense == minimize:
            self._solver_model.Minimize(cpsat_expr)
        elif obj.sense == maximize:
            self._solver_model.Maximize(cpsat_expr)
        else:
            raise ValueError(f'Objective sense is not recognized: {obj.sense}')

        self._objective = obj
        self._vars_referenced_by_obj = referenced_vars

    def _apply_solver(self):
        StaleFlagManager.mark_all_as_stale()

        if self._tee:
            self._solver_solver.parameters.log_search_progress = True
        else:
            self._solver_solver.parameters.log_search_progress = False

        # if self._keepfiles:
        #     # Only save log file when the user wants to keep it.
        #     self._solver_model.setParam('LogFile', self._log_file)
        #     print("Solver log file: " + self._log_file)

        # # Options accepted by gurobi (case insensitive):
        # for key, option in self.options.items():
        #     # When options come from the pyomo command, all
        #     # values are string types, so we try to cast
        #     # them to a numeric value in the event that
        #     # setting the parameter fails.
        #     try:
        #         self._solver_model.setParam(key, option)
        #     except TypeError:
        #         # we place the exception handling for
        #         # checking the cast of option to a float in
        #         # another function so that we can simply
        #         # call raise here instead of except
        #         # TypeError as e / raise e, because the
        #         # latter does not preserve the Gurobi stack
        #         # trace
        #         if not _is_numeric(option):
        #             raise
        #         self._solver_model.setParam(key, float(option))

        self._solver_status = self._solver_solver.Solve(self._solver_model)

        return Bunch(rc=None, log=None)

    def _postsolve(self):
        # Disable extraction of all suffixes
        if self._suffixes:
            raise RuntimeError(
                "***The cpsat solver interface cannot extract solution suffixes"
            )

        cpsat_model = self._solver_model
        cpsat_model_proto = self._solver_model.Proto()
        cpsat_solver = self._solver_solver
        status = self._solver_status

        self.results = SolverResults()
        soln = Solution()

        # self.results.solver.name = GurobiDirect._name
        self.results.solver.wallclock_time = cpsat_solver.WallTime()

        if status == cp_model.UNKNOWN:
            self.results.solver.status = SolverStatus.warning
            self.results.solver.termination_message = (
                'The status of the model is unknown, because no solution was '
                'found or the problem was not proven infeasible before the '
                ' solver stopped.'
            )
            self.results.solver.termination_condition = TerminationCondition.unknown
            soln.status = SolutionStatus.unknown
        elif status == cp_model.OPTIMAL:
            self.results.solver.status = SolverStatus.ok
            self.results.solver.termination_message = (
                'An optimal feasible solution was found.'
            )
            self.results.solver.termination_condition = TerminationCondition.optimal
            soln.status = SolutionStatus.optimal
        elif status == cp_model.FEASIBLE:
            self.results.solver.status = SolverStatus.warning
            self.results.solver.termination_message = (
                'A feasible solution was found, but we do not know if it is optimal.'
            )
            self.results.solver.termination_condition = TerminationCondition.feasible
            soln.status = SolutionStatus.feasible

        elif status == cp_model.INFEASIBLE:
            self.results.solver.status = SolverStatus.warning
            self.results.solver.termination_message = (
               'The problem was proven infeasible.'
            )
            self.results.solver.termination_condition = TerminationCondition.infeasible
            soln.status = SolutionStatus.infeasible
        elif status == cp_model.MODEL_INVALID:
            self.results.solver.status = SolverStatus.aborted
            self.results.solver.termination_message = (
                'The given model did not pass the validation step.'
            )
            self.results.solver.termination_condition = TerminationCondition.invalidProblem
            soln.status = SolutionStatus.error
        else:
            self.results.solver.status = SolverStatus.error
            self.results.solver.termination_message = (
                "Unhandled CP-SAT solver status (" + str(status) + ")"
            )
            self.results.solver.termination_condition = TerminationCondition.error
            soln.status = SolutionStatus.error

        self.results.problem.name = ''

        if cpsat_model_proto.objective.scaling_factor > 0:
            self.results.problem.sense = minimize
        elif cpsat_model_proto.objective.scaling_factor < 0:
            self.results.problem.sense = maximize
        else:
            raise RuntimeError(
                'Unrecognized CP-SAT objective sense - scaling_factor = {0}'
                .format(cpsat_model.__model.objective.scaling_factor)
            )

        self.results.problem.upper_bound = None
        self.results.problem.lower_bound = None

        if self.results.problem.sense == minimize:
            self.results.problem.upper_bound = self._solver_solver.BestObjectiveBound()
            self.results.problem.lower_bound = self._solver_solver.ObjectiveValue()
        elif self.results.problem.sense == maximize:
            self.results.problem.upper_bound = self._solver_solver.ObjectiveValue()
            self.results.problem.lower_bound = self._solver_solver.BestObjectiveBound()

        try:
            soln.gap = (
                self.results.problem.upper_bound - self.results.problem.lower_bound
            )
        except TypeError:
            soln.gap = None

        # These are all messed up
        number_of_binary_variables = 0
        number_of_integer_variables = 0
        for var in cpsat_model_proto.variables:
            if len(var.domain) == 2 and var.domain[0] == 0 and var.domain[1] == 1:
                number_of_binary_variables += 1
            else:
                number_of_integer_variables +=1

        self.results.problem.number_of_constraints = len(cpsat_model_proto.constraints)
        self.results.problem.number_of_variables = len(cpsat_model_proto.variables)
        self.results.problem.number_of_binary_variables = number_of_binary_variables
        self.results.problem.number_of_integer_variables = number_of_integer_variables
        self.results.problem.number_of_continuous_variables = 0
        self.results.problem.number_of_objectives = 1
        # TODO: can't find a way to get this in the Python API without a callback
        self.results.problem.number_of_solutions = None
        # TODO: can't find a way to get this easily in the Python API
        self.results.problem.number_of_nonzeros = None

        if self._save_results:
            if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                self.load_vars()

        self.results.solution.insert(soln)

        # # finally, clean any temporary files registered with the temp file
        # # manager, created populated *directly* by this plugin.
        # TempfileManager.pop(remove=not self._keepfiles)

        return DirectOrPersistentSolver._postsolve(self)

    def _load_vars(self, vars_to_load=None):
        var_map = self._pyomo_var_to_solver_var_map
        ref_vars = self._referenced_variables
        if vars_to_load is None:
            vars_to_load = var_map.keys()

        for pyomo_var in vars_to_load:
            if ref_vars[pyomo_var] > 0:
                cpsat_var = var_map[pyomo_var]
                cpsat_val = self._solver_solver.Value(cpsat_var)
                pyomo_var.set_value(cpsat_val, skip_validation=True)
