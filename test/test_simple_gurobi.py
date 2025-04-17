import pyomo.environ as pyo
from model import SimpleModel

simple = SimpleModel()

solver = pyo.SolverFactory('gurobi')
solver.solve(simple.model, tee=True)

print('\nObjective value:', pyo.value(simple.model.obj))

print('\nOptimal solution:')
for k in simple.model.K:
    print(f'x[{k}] = {simple.model.x[k].value}')
