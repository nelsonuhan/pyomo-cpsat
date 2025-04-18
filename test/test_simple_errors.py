import math
import pytest
import pyomo.environ as pyo
from pyomo.contrib.solver.common.util import (
    NoFeasibleSolutionError,
    NoOptimalSolutionError,
)
from pyomo_cpsat import Cpsat, IncompatibleModelError
from model import SimpleModel

simple = SimpleModel()
simple_real_vars = SimpleModel(real_vars=True)
simple_nolb_vars = SimpleModel(nolb_vars=True)
simple_noub_vars = SimpleModel(noub_vars=True)
simple_quad_con = SimpleModel(quad_con=True)
simple_nonlinear_con = SimpleModel(nonlinear_con=True)
simple_quad_obj = SimpleModel(quad_obj=True)
simple_nonlinear_obj = SimpleModel(nonlinear_obj=True)


solver = Cpsat()


## Start tests
def test_pyomo_equivalent_keys_threads():
    with pytest.raises(ValueError):
        solver.solve(
            simple.model,
            threads=1,
            solver_options={
                'num_workers': 1,
            },
        )


def test_pyomo_equivalent_keys_time_limit():
    with pytest.raises(ValueError):
        solver.solve(
            simple.model,
            time_limit=100,
            solver_options={
                'max_time_in_seconds': 100,
            },
        )


def test_pyomo_equivalent_keys_rel_gap():
    with pytest.raises(ValueError):
        solver.solve(
            simple.model,
            rel_gap=0.0,
            solver_options={
                'relative_gap_limit': 0.0,
            },
        )


def test_pyomo_equivalent_keys_abs_gap():
    with pytest.raises(ValueError):
        solver.solve(
            simple.model,
            abs_gap=1e-4,
            solver_options={
                'absolute_gap_limit': 1e-4,
            },
        )


def test_real_vars():
    with pytest.raises(ValueError):
        solver.solve(simple_real_vars.model)


def test_nolb_vars():
    with pytest.raises(ValueError):
        solver.solve(simple_nolb_vars.model)


def test_noub_vars():
    with pytest.raises(ValueError):
        solver.solve(simple_noub_vars.model)


def test_quad_con():
    with pytest.raises(IncompatibleModelError):
        solver.solve(simple_quad_con.model)


def test_nonlinear_con():
    with pytest.raises(IncompatibleModelError):
        solver.solve(simple_nonlinear_con.model)


def test_quad_obj():
    with pytest.raises(IncompatibleModelError):
        solver.solve(simple_quad_obj.model)


def test_nonlinear_obj():
    with pytest.raises(IncompatibleModelError):
        solver.solve(simple_nonlinear_obj.model)
