"""
Compute optimal solution and optimal value for SimpleModel to use in tests
"""

import pyomo.environ as pyo
from model import SimpleModel

simple = SimpleModel()

#
# Solve model
#
solver = pyo.SolverFactory('glpk')
solver.solve(simple.model, tee=True)

print('\nObjective value:', pyo.value(simple.model.obj))

print('\nOptimal solution:')
for k in simple.model.K:
    print(f'x[{k}] = {simple.model.x[k].value}')

#
# Solve model with x['vanilla'] fixed to 1
#
simple.model.x['vanilla'].fix(2)
solver.solve(simple.model, tee=True)

print('\nObjective value:', pyo.value(simple.model.obj))

print('\nOptimal solution:')
for k in simple.model.K:
    print(f'x[{k}] = {simple.model.x[k].value}')
