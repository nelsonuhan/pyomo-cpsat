# pyomo-cpsat

A [Pyomo](https://pyomo.readthedocs.io/en/stable/index.html) direct interface
to the [CP-SAT](https://developers.google.com/optimization/cp/cp_solver) solver.

pyomo-cpsat is limited to solving __pure integer linear programs__ with CP-SAT,
or optimization models with

* a linear objective function with real coefficients,
* linear constraints with integral coefficients, and
* bounded integer variables.

pyomo-cpsat does __not__ implement other CP-SAT constraint types, such as
[cumulative constraints](https://developers.google.com/optimization/reference/python/sat/python/cp_model#addcumulative),
[reservoir constraints](https://developers.google.com/optimization/reference/python/sat/python/cp_model#addreservoirconstraint),
etc.

Through a keyword argument, pyomo-cpsat can find infeasible subsystems of
constraints for infeasible models, using the approach
[illustrated here](https://github.com/google/or-tools/blob/master/ortools/sat/samples/assumptions_sample_sat.py).

pyomo-cpsat is currently experimental - it is based on the future Pyomo solver
interface [documented here](https://pyomo.readthedocs.io/en/stable/explanation/experimental/solvers.html),
still under active development.

## Usage

Here's an example of using pyomo-cpsat to solve a simple model.

```python
import pyomo.environ as pyo
from pyomo.contrib.solver.common.factory import SolverFactory
import pyomo_cpsat

model = pyo.ConcreteModel()

model.I = pyo.Set(initialize=[1, 2, 3])
model.w = pyo.Param(model.I, initialize={1: 10, 2: 20, 3: 30})
model.x = pyo.Var(model.I, domain=pyo.Integers, bounds=(0, 100))

def con_rule(model):
    return pyo.quicksum(model.w[i] * model.x[i] for i in model.I) <= 20

model.con = pyo.Constraint(rule=con_rule)

def obj_rule(model):
    return pyo.quicksum(model.x[i] for i in model.I)

model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

solver = SolverFactory('cpsat')
results = solver.solve(
    model,
    tee=True,           # sets log_search_progress in CP-SAT
    threads=8,          # sets num_workers in CP-SAT
    time_limit=300,     # sets max_time_in_seconds in CP-SAT
    rel_gap=0.1,        # sets relative_gap_limit in CP-SAT
    abs_gap=1e-6,       # sets absolute_gap_limit in CP-SAT
    solver_options = {  # set CP-SAT parameters directly
        'subsolvers': ['pseudo_costs', 'probing']
    }
)
results.display()
```

Here's an example of using pyomo-cpsat to find an infeasible subsystem of
constraints for an infeasible model:

```python
import pyomo.environ as pyo
from pyomo.contrib.solver.common.factory import SolverFactory
import pyomo_cpsat

model = pyo.ConcreteModel()

model.I = pyo.Set(initialize=[1, 2, 3])
model.w = pyo.Param(model.I, initialize={1: 10, 2: 20, 3: 30})
model.x = pyo.Var(model.I, domain=pyo.Integers, bounds=(10, 100))

def infeasible_con_rule(model):
    return pyo.quicksum(model.w[i] * model.x[i] for i in model.I) <= 20

model.infeasible_con = pyo.Constraint(rule=infeasible_con_rule)

def obj_rule(model):
    return pyo.quicksum(model.x[i] for i in model.I)

model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

solver = SolverFactory('cpsat')
results = solver.solve(model, find_infeasible_subsystem=True)
```
