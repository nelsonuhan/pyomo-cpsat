import pytest
import pyomo.environ as pyo
from pyomo.contrib.solver.common.results import SolutionStatus, TerminationCondition
from pyomo.contrib.solver.common.util import (
    NoFeasibleSolutionError,
    NoOptimalSolutionError,
)
from pyomo_cpsat import Cpsat, IncompatibleModelError
from model import (
    SimpleModel,
    MinObjModel,
    MaxObjModel,
    RealVarsModel,
    NoLbVarsModel,
    NoUbVarsModel,
    QuadConModel,
    NonlinearConModel,
    QuadObjModel,
    NonlinearObjModel,
    InfeasibleModel,
    InactiveConModel,
    ConstantObjModel,
)


solver = Cpsat()


## Start tests
def test_max_objective():
    maxobj = MaxObjModel()
    solver.solve(maxobj.model)
    assert solver._solver_model.proto.objective.scaling_factor < 0


def test_min_objective():
    minobj = MinObjModel()
    solver.solve(minobj.model)
    assert solver._solver_model.proto.objective.scaling_factor >= 0


def test_solver_options():
    simple = SimpleModel()
    solver.solve(simple.model, solver_options={'num_full_subsolvers': 2})
    assert solver._solver_solver.parameters.num_full_subsolvers == 2


def test_solver_options_repeating():
    simple = SimpleModel()
    solver.solve(
        simple.model,
        solver_options={'subsolvers': ['pseudo_costs', 'probing']},
    )
    assert solver._solver_solver.parameters.subsolvers == ['pseudo_costs', 'probing']


def test_pyomo_equivalent_keys_threads():
    with pytest.raises(KeyError):
        simple = SimpleModel()
        solver.solve(
            simple.model,
            threads=1,
            solver_options={
                'num_workers': 1,
            },
        )


def test_pyomo_equivalent_keys_time_limit():
    with pytest.raises(KeyError):
        simple = SimpleModel()
        solver.solve(
            simple.model,
            time_limit=100,
            solver_options={
                'max_time_in_seconds': 100,
            },
        )


def test_pyomo_equivalent_keys_rel_gap():
    with pytest.raises(KeyError):
        simple = SimpleModel()
        solver.solve(
            simple.model,
            rel_gap=0.0,
            solver_options={
                'relative_gap_limit': 0.0,
            },
        )


def test_pyomo_equivalent_keys_abs_gap():
    with pytest.raises(KeyError):
        simple = SimpleModel()
        solver.solve(
            simple.model,
            abs_gap=1e-4,
            solver_options={
                'absolute_gap_limit': 1e-4,
            },
        )


def test_realvars():
    with pytest.raises(IncompatibleModelError):
        realvars = RealVarsModel()
        solver.solve(realvars.model)


def test_nolbvars():
    with pytest.raises(IncompatibleModelError):
        nolb = NoLbVarsModel()
        solver.solve(nolb.model)


def test_noubvars():
    with pytest.raises(IncompatibleModelError):
        noub = NoUbVarsModel()
        solver.solve(noub.model)


def test_quadcon():
    with pytest.raises(IncompatibleModelError):
        quadcon = QuadConModel()
        solver.solve(quadcon.model)


def test_nonlinearcon():
    with pytest.raises(IncompatibleModelError):
        nonlinearcon = NonlinearConModel()
        solver.solve(nonlinearcon.model)


def test_quadobj():
    with pytest.raises(IncompatibleModelError):
        quadobj = QuadObjModel()
        solver.solve(quadobj.model)


def test_nonlinearobj():
    with pytest.raises(IncompatibleModelError):
        nonlinearobj = NonlinearObjModel()
        solver.solve(nonlinearobj.model)


def test_infeasible_1():
    """
    raise_exception_on_nonoptimal_result = True (default)
    load_solutions = True (default)
    """
    with pytest.raises(NoOptimalSolutionError):
        infeasible = InfeasibleModel()
        solver.solve(infeasible.model)


def test_infeasible_2():
    """
    raise_exception_on_nonoptimal_result = False
    load_solutions = True (default)
    """
    with pytest.raises(NoFeasibleSolutionError):
        infeasible = InfeasibleModel()
        solver.solve(infeasible.model, raise_exception_on_nonoptimal_result=False)


def test_infeasible_3():
    """
    raise_exception_on_nonoptimal_result = False
    load_solutions = False
    """
    infeasible = InfeasibleModel()
    results = solver.solve(
        infeasible.model,
        raise_exception_on_nonoptimal_result=False,
        load_solutions=False,
    )

    assert (results.solution_status == SolutionStatus.infeasible) and (
        results.termination_condition == TerminationCondition.provenInfeasible
    )


def test_inactive():
    """
    Solve a model with 2 constraints, 1 of which is inactive.
    Pyomo should only pass 1 constraint to CP-SAT.
    """
    inactive = InactiveConModel()
    solver.solve(inactive.model)
    assert len(solver._solver_model.proto.constraints) == 1


def test_constantobj():
    constantobj = ConstantObjModel()
    solver.solve(constantobj.model)
    assert pyo.value(constantobj.model.obj) == 500


def test_inactive_obj():
    with pytest.raises(ValueError):
        simple = SimpleModel()
        simple.model.obj.deactivate()
        solver.solve(simple.model)
