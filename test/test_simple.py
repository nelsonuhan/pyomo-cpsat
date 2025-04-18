import math
import pyomo.environ as pyo
from pyomo.contrib.solver.common.base import Availability
from pyomo.contrib.solver.common.results import SolutionStatus, TerminationCondition
from pyomo_cpsat import Cpsat
from model import SimpleModel

simple = SimpleModel()

solver = Cpsat()

results = solver.solve(
    simple.model,
    tee=False,
    threads=1,
    time_limit=100,
    rel_gap=0.0,
    abs_gap=1e-4,
    load_solutions=True,
)


## Start tests
def test_available():
    assert solver.available() == Availability.FullLicense


def test_version():
    assert len(solver.version()) == 3


def test_persistent():
    assert not solver.is_persistent()


def test_tee():
    assert not solver._solver_solver.parameters.log_search_progress


def test_threads():
    assert solver._solver_solver.parameters.num_workers == 1


def test_time_limit():
    assert solver._solver_solver.parameters.max_time_in_seconds == 100


def test_rel_gap():
    assert math.isclose(solver._solver_solver.parameters.relative_gap_limit, 0.0)


def test_abs_gap():
    assert math.isclose(solver._solver_solver.parameters.absolute_gap_limit, 1e-4)


def test_solution_status():
    assert results.solution_status == SolutionStatus.optimal


def test_termination_condition():
    assert (
        results.termination_condition
        == TerminationCondition.convergenceCriteriaSatisfied
    )


def test_objective_value():
    assert pyo.value(simple.model.obj) == 196


def test_solution():
    assert (
        simple.model.x['chocolate'].value == 2
        and simple.model.x['vanilla'].value == 0
        and simple.model.x['matcha'].value == 8
    )


# # print('Timing', [(k, v) for k, v in results.timing_info.items()])
