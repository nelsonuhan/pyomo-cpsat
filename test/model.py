import pyomo.environ as pyo


class SimpleModel:
    def __init__(self):
        cake_types = ['chocolate', 'vanilla', 'matcha']
        ingredients = ['eggs', 'flour']

        prices = {'chocolate': 3, 'vanilla': 4, 'matcha': 5}

        available_ingredients = {'eggs': 32, 'flour': 48}

        recipes = {
            ('eggs', 'chocolate'): 4,
            ('eggs', 'vanilla'): 2,
            ('eggs', 'matcha'): 3,
            ('flour', 'chocolate'): 4,
            ('flour', 'vanilla'): 6,
            ('flour', 'matcha'): 5,
        }

        self.model = pyo.ConcreteModel()

        self.model.K = pyo.Set(initialize=cake_types)
        self.model.I = pyo.Set(initialize=ingredients)

        self.model.p = pyo.Param(self.model.K, initialize=prices)
        self.model.b = pyo.Param(self.model.I, initialize=available_ingredients)
        self.model.a = pyo.Param(self.model.I, self.model.K, initialize=recipes)

        self.model.x = pyo.Var(
            self.model.K, domain=pyo.NonNegativeIntegers, bounds=(0, 100)
        )

        self.model.total_cakes = pyo.Expression(
            expr=pyo.quicksum(self.model.x[k] for k in self.model.K)
        )

        def obj_rule(model):
            return 150 + sum(model.p[k] * model.x[k] for k in model.K)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

        def ingredients_available_rule(model, i):
            return sum(model.a[i, k] * model.x[k] for k in model.K) <= model.b[i]

        self.model.ingredients_available_con = pyo.Constraint(
            self.model.I, rule=ingredients_available_rule
        )

        def total_cakes_rule(model):
            return model.total_cakes <= 10

        self.model.total_cakes_con = pyo.Constraint(rule=total_cakes_rule)
