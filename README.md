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

## Examples

### Solving a simple model

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
    tee=False,          # sets log_search_progress in CP-SAT
    threads=8,          # sets num_workers in CP-SAT
    time_limit=300,     # sets max_time_in_seconds in CP-SAT
    rel_gap=0.1,        # sets relative_gap_limit in CP-SAT
    abs_gap=1e-6,       # sets absolute_gap_limit in CP-SAT
    solver_options={    # passes CP-SAT parameters
        'subsolvers': ['pseudo_costs', 'probing']
    },
)

print(f'Termination condition: {results.termination_condition}')
print(f'Solution status: {results.solution_status}')
print('Solution:')
for i in model.I:
    print(f'  x[{i}] = {pyo.value(model.x[i])}')
```

Resulting output:

```
Termination condition: TerminationCondition.convergenceCriteriaSatisfied
Solution status: SolutionStatus.optimal
Solution:
  x[1] = 2
  x[2] = 0
  x[3] = 0
```

### Finding an infeasible subsystem of constraints

```python
import pyomo.environ as pyo
from pyomo.contrib.solver.common.factory import SolverFactory
import pyomo_cpsat

model = pyo.ConcreteModel()

model.I = pyo.Set(initialize=[1, 2, 3])
model.K = pyo.Set(initialize=['a', 'b'])
model.a = pyo.Param(
    model.K,
    model.I,
    initialize={
        ('a', 1): 1,
        ('a', 2): 2,
        ('a', 3): 3,
        ('b', 1): -1,
        ('b', 2): -1,
        ('b', 3): -1,
    },
)
model.b = pyo.Param(
    model.K,
    initialize={'a': 5, 'b': -10},
)

model.x = pyo.Var(model.I, domain=pyo.Integers, bounds=(0, 1))

def con_rule(model, k):
    return pyo.quicksum(model.a[k, i] * model.x[i] for i in model.I) <= model.b[k]

model.con = pyo.Constraint(model.K, rule=con_rule)

def obj_rule(model):
    return pyo.quicksum(model.x[i] for i in model.I)

model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

solver = SolverFactory('cpsat')
results = solver.solve(model, find_infeasible_subsystem=True)
```

Resulting output:

```
Infeasible subsystem of constraints
-----------------------------------
con[b]
```
