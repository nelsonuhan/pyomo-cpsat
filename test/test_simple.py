import pyomo.environ as pyo
from pyomo_cpsat import Cpsat

K_list = ['chocolate', 'vanilla']
I_list = ['eggs', 'flour']

p_dict = {'chocolate': 3, 'vanilla': 4}

b_dict = {'eggs': 32, 'flour': 48}

a_dict = {
    ('eggs', 'chocolate'): 4,
    ('eggs', 'vanilla'): 2,
    ('flour', 'chocolate'): 4,
    ('flour', 'vanilla'): 6,
}


model = pyo.ConcreteModel()

model.K = pyo.Set(initialize=K_list)
model.I = pyo.Set(initialize=I_list)

model.p = pyo.Param(model.K, initialize=p_dict)
model.b = pyo.Param(model.I, initialize=b_dict)
model.a = pyo.Param(model.I, model.K, initialize=a_dict)

model.x = pyo.Var(model.K, domain=pyo.NonNegativeIntegers, bounds=(0, 100))

model.total_ingredients = pyo.Expression(expr=pyo.quicksum(model.x[k] for k in model.K))


def obj_rule(model):
    return 5 + sum(model.p[k] * model.x[k] for k in model.K)


model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)


def ingredients_available_rule(model, i):
    return sum(model.a[i, k] * model.x[k] for k in model.K) <= model.b[i]


model.ingredients_available = pyo.Constraint(model.I, rule=ingredients_available_rule)


def test_rule(model):
    return model.total_ingredients <= 100000


model.test_con = pyo.Constraint(rule=test_rule)

solver = Cpsat()
print('Available', solver.available())
print('Version', solver.version())
print('Is persistent', solver.is_persistent())
# solver.set_instance(model)
results = solver.solve(
    model,
    tee=False,
    threads=1,
    time_limit=100,
    rel_gap=0.0,
    abs_gap=1e-4,
    load_solutions=True,
    # solver_options={
    #     'num_workers': 1,
    #     'max_time_in_seconds': 100,
    #     'absolute_gap_limit': 1e-4,
    #     'relative_gap_limit': 0.0,
    # },
)
print('CP-SAT variables')
for v in solver._solver_model.proto.variables:
    print(v)
print('CP-SAT constraints')
for c in solver._solver_model.proto.constraints:
    print(c)
print('CP-SAT objective')
solver._solver_model.proto.objective
print('Solution status', results.solution_status)
print('Termination condition', results.termination_condition)
# print('Timing', [(k, v) for k, v in results.timing_info.items()])
print('Incumbent objective', results.incumbent_objective)
print('Objective bound', results.objective_bound)

# for k in model.K:
#     print(f'x[{k}] = {model.x[k].value}')
