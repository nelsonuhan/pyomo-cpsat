import pyomo.environ as pyo
# from cpsat import CpsatInterface
from appsi_cpsat import Highs


nodes = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}

edges = {(0, 1), (0, 2), (0, 3), (1, 4),
         (1, 6), (2, 1), (2, 3), (2, 5),
         (3, 5), (4, 2), (5, 7), (5, 8),
         (6, 4), (6, 7), (6, 9), (7, 4),
         (7, 9), (8, 3), (8, 7), (8, 9)}

distance = {(0, 1): 40, (0, 2):  8, (0, 3): 10, (1, 4):  6,
            (1, 6): 10, (2, 1):  4, (2, 3): 12, (2, 5):  2,
            (3, 5):  1, (4, 2):  2, (5, 7):  4, (5, 8):  3,
            (6, 4):  8, (6, 7): 20, (6, 9):  1, (7, 4):  0,
            (7, 9): 20, (8, 3):  6, (8, 7): 10, (8, 9):  2}

source = 0
sink = 9

model = pyo.ConcreteModel()

model.x = pyo.Var(edges, domain=pyo.Binary)

@model.Objective(sense=pyo.minimize)
def total_distance(m):
    return sum(distance[i, j] * m.x[i, j] for (i, j) in edges)

@model.Constraint(nodes)
def flow_balance(m, i):
    flow_in =  sum(m.x[j, k] for (j, k) in edges if k == i)
    flow_out = sum(m.x[j, k] for (j, k) in edges if j == i)

    if i == source:
        return flow_out == 1
    elif i == sink:
        return flow_in == 1
    else:
        return flow_in == flow_out

model.write('test.mps', 'mps')

solver = pyo.SolverFactory('appsi_highs_nelson')
# solver = pyo.SolverFactory('gurobi')
# solver = pyo.SolverFactory('scip')
# solver = pyo.SolverFactory('appsi_highs')
# solver = pyo.SolverFactory('appsi_gurobi')

result = solver.solve(model, tee=True)


