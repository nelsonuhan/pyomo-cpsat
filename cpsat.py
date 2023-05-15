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

CPSAT_INFINITY = 1000000

class DegreeError(ValueError):
    pass


@SolverFactory.register('cpsat', doc='Direct Python interface to CP-SAT')
class CpsatDirect(DirectSolver):
    def __init__(self, **kwds):
        if 'type' not in kwds:
            kwds['type'] = 'cpsat_direct'

        super(CpsatDirect, self).__init__(**kwds)

    def available(self, exception_flag=True):
        return True

    def license_is_valid(self):
        return True

    def version(self):
        return (0, 0, 0)

    def _apply_solver(self):
        pass

    def _get_expr_from_pyomo_repn(self, repn: StandardRepn, max_degree=1):
        referenced_vars = ComponentSet()

        degree = repn.polynomial_degree()
        if (degree is None) or (degree > max_degree):
            raise DegreeError(
                f'CpsatDirect does not support expressions of degree {degree}.'
            )

        if len(repn.linear_vars) > 0:
            referenced_vars.update(repn.linear_vars)
            cpsat_expr = cp_model.LinearExpr.ScalProd(
                [self._pyomo_var_to_solver_var_map[i] for i in repn.linear_vars],
                repn.linear_coefs
            )
        else:
            cpsat_expr = 0.0

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
        varname = self._symbol_map.getSymbol(var, self._labeler)
        lb, ub = self._cpsat_bounds_from_var(var)

        cpsat_var = self._solver_model.NewIntVar(lb, ub, varname)

        self._pyomo_var_to_solver_var_map[var] = cpsat_var
        self._solver_var_to_pyomo_var_map[cpsat_var] = var
        self._referenced_variables[var] = 0

        self._needs_updated = True

    def _set_instance(self, model, kwds={}):
        self._range_constraints = set()
        DirectOrPersistentSolver._set_instance(self, model, kwds)
        self._pyomo_con_to_solver_con_map = dict()
        self._solver_con_to_pyomo_con_map = ComponentMap()
        self._pyomo_var_to_solver_var_map = ComponentMap()
        self._solver_var_to_pyomo_var_map = ComponentMap()
        self._solver_model = cp_model.CpModel()

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

        # if con._linear_canonical_form:
        #     gurobi_expr, referenced_vars = self._get_expr_from_pyomo_repn(
        #         con.canonical_form(), self._max_constraint_degree
        #     )
        # # elif isinstance(con, LinearCanonicalRepn):
        # #    gurobi_expr, referenced_vars = self._get_expr_from_pyomo_repn(
        # #        con,
        # #        self._max_constraint_degree)
        # else:
        #     gurobi_expr, referenced_vars = self._get_expr_from_pyomo_expr(
        #         con.body, self._max_constraint_degree
        #     )

        # if con.has_lb():
        #     if not is_fixed(con.lower):
        #         raise ValueError(
        #             "Lower bound of constraint {0} is not constant.".format(con)
        #         )
        # if con.has_ub():
        #     if not is_fixed(con.upper):
        #         raise ValueError(
        #             "Upper bound of constraint {0} is not constant.".format(con)
        #         )

        # if con.equality:
        #     gurobipy_con = self._solver_model.addConstr(
        #         lhs=gurobi_expr,
        #         sense=gurobipy.GRB.EQUAL,
        #         rhs=value(con.lower),
        #         name=conname,
        #     )
        # elif con.has_lb() and con.has_ub():
        #     gurobipy_con = self._solver_model.addRange(
        #         gurobi_expr, value(con.lower), value(con.upper), name=conname
        #     )
        #     self._range_constraints.add(con)
        # elif con.has_lb():
        #     gurobipy_con = self._solver_model.addConstr(
        #         lhs=gurobi_expr,
        #         sense=gurobipy.GRB.GREATER_EQUAL,
        #         rhs=value(con.lower),
        #         name=conname,
        #     )
        # elif con.has_ub():
        #     gurobipy_con = self._solver_model.addConstr(
        #         lhs=gurobi_expr,
        #         sense=gurobipy.GRB.LESS_EQUAL,
        #         rhs=value(con.upper),
        #         name=conname,
        #     )
        # else:
        #     raise ValueError(
        #         "Constraint does not have a lower "
        #         "or an upper bound: {0} \n".format(con)
        #     )

        # for var in referenced_vars:
        #     self._referenced_variables[var] += 1
        # self._vars_referenced_by_con[con] = referenced_vars
        # self._pyomo_con_to_solver_con_map[con] = gurobipy_con
        # self._solver_con_to_pyomo_con_map[gurobipy_con] = con

        # self._needs_updated = True
