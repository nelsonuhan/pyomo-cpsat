# pyomo-cpsat

A [Pyomo](https://pyomo.readthedocs.io/en/stable/index.html) direct interface
to the [CP-SAT](https://developers.google.com/optimization/cp/cp_solver) solver.

Note: pyomo-cpsat is limited to solving __pure integer linear programs__
with CP-SAT, or optimization models with

* a linear objective function with real coefficients,
* linear constraints with integral coefficients, and
* bounded integer variables.

pyomo-cpsat does __not__ implement other CP-SAT constraint types, such as
[cumulative constraints](https://developers.google.com/optimization/reference/python/sat/python/cp_model#addcumulative),
[reservoir constraints](https://developers.google.com/optimization/reference/python/sat/python/cp_model#addreservoirconstraint),
etc.

pyomo-cpsat is currently experimental, based on the future Pyomo solver interface changes
[documented here](https://pyomo.readthedocs.io/en/stable/explanation/experimental/solvers.html).

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
results = solver.solve(model)
results.display()
```

