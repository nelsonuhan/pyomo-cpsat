import math
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
)


solver = Cpsat()


## Start tests
def test_pyomo_equivalent_keys_threads():
    with pytest.raises(ValueError):
        simple = SimpleModel()
        solver.solve(
            simple.model,
            threads=1,
            solver_options={
                'num_workers': 1,
            },
        )


def test_pyomo_equivalent_keys_time_limit():
    with pytest.raises(ValueError):
        simple = SimpleModel()
        solver.solve(
            simple.model,
            time_limit=100,
            solver_options={
                'max_time_in_seconds': 100,
            },
        )


def test_pyomo_equivalent_keys_rel_gap():
    with pytest.raises(ValueError):
        simple = SimpleModel()
        solver.solve(
            simple.model,
            rel_gap=0.0,
            solver_options={
                'relative_gap_limit': 0.0,
            },
        )


def test_pyomo_equivalent_keys_abs_gap():
    with pytest.raises(ValueError):
        simple = SimpleModel()
        solver.solve(
            simple.model,
            abs_gap=1e-4,
            solver_options={
                'absolute_gap_limit': 1e-4,
            },
        )


def test_realvars():
    with pytest.raises(ValueError):
        realvars = RealVarsModel()
        solver.solve(realvars.model)


def test_nolbvars():
    with pytest.raises(ValueError):
        nolb = NoLbVarsModel()
        solver.solve(nolb.model)


def test_noubvars():
    with pytest.raises(ValueError):
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
