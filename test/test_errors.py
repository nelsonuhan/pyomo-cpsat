import math
from pyomo.contrib.solver.common.results import SolutionStatus, TerminationCondition
import pytest
import pyomo.environ as pyo
from pyomo.contrib.solver.common.util import (
    NoFeasibleSolutionError,
    NoOptimalSolutionError,
)
from pyomo_cpsat import Cpsat, IncompatibleModelError
from model import (
    SimpleModel,
    RealVarsModel,
    NoLbVarsModel,
    NoUbVarsModel,
    QuadConModel,
    NonlinearConModel,
    QuadObjModel,
    NonlinearObjModel,
    InfeasibleModel,
)


solver = Cpsat()


## Start tests
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
