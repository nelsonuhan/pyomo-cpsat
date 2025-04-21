import math
import pyomo.environ as pyo
import pytest
from pyomo.contrib.solver.common.factory import SolverFactory
from pyomo.contrib.solver.common.base import Availability
from pyomo.contrib.solver.common.results import SolutionStatus, TerminationCondition
from pyomo.contrib.solver.common.util import (
    NoFeasibleSolutionError,
    NoOptimalSolutionError,
)
from pyomo.opt import Solution
from pytest import raises
import pyomo_cpsat
from model import SimpleModel

simple = SimpleModel()

# Fix x['vanilla'] to 2
simple.model.x['vanilla'].fix(2)

solver = pyomo_cpsat.Cpsat()

results = solver.solve(
    simple.model,
    tee=True,
    threads=1,
    time_limit=100,
    rel_gap=0.0,
    abs_gap=1e-4,
    load_solutions=True,
)


## Start tests
def test_solution_fix():
    assert (
        simple.model.x['chocolate'].value == 0
        and simple.model.x['vanilla'].value == 2
        and simple.model.x['matcha'].value == 7
    )


def test_objective_value_fix():
    assert pyo.value(simple.model.obj) == 193
