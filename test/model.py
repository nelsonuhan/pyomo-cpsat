import pyomo.environ as pyo


class SimpleModel:
    def __init__(
        self,
        real_vars=False,
        nolb_vars=False,
        noub_vars=False,
        quad_con=False,
        nonlinear_con=False,
        quad_obj=False,
        nonlinear_obj=False,
    ):
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

        #
        # Sets
        #
        self.model.K = pyo.Set(initialize=cake_types)
        self.model.I = pyo.Set(initialize=ingredients)

        #
        # Parameters
        #
        self.model.p = pyo.Param(self.model.K, initialize=prices)
        self.model.b = pyo.Param(self.model.I, initialize=available_ingredients)
        self.model.a = pyo.Param(self.model.I, self.model.K, initialize=recipes)

        #
        # Variables
        #
        if real_vars:
            x_domain = pyo.Reals
        else:
            x_domain = pyo.Integers

        if nolb_vars:
            x_lb = None
        else:
            x_lb = 0

        if noub_vars:
            x_ub = None
        else:
            x_ub = 100

        self.model.x = pyo.Var(self.model.K, domain=x_domain, bounds=(x_lb, x_ub))

        #
        # Constraints
        #
        self.model.total_cakes = pyo.Expression(
            expr=pyo.quicksum(self.model.x[k] for k in self.model.K)
        )

        def ingredients_available_rule(model, i):
            return (
                pyo.quicksum(model.a[i, k] * model.x[k] for k in model.K) <= model.b[i]
            )

        self.model.ingredients_available_con = pyo.Constraint(
            self.model.I, rule=ingredients_available_rule
        )

        def total_cakes_rule(model):
            return model.total_cakes <= 10

        self.model.total_cakes_con = pyo.Constraint(rule=total_cakes_rule)

        def quad_rule(model):
            return pyo.quicksum(model.x[k] ** 2 for k in model.K) >= 0

        self.model.quad_con = pyo.Constraint(rule=quad_rule)

        def nonlinear_rule(model):
            return pyo.quicksum(pyo.sin(model.x[k]) for k in model.K) >= 0

        self.model.nonlinear_con = pyo.Constraint(rule=nonlinear_rule)

        if quad_con:
            self.model.quad_con.activate()
        else:
            self.model.quad_con.deactivate()

        if nonlinear_con:
            self.model.nonlinear_con.activate()
        else:
            self.model.nonlinear_con.deactivate()

        #
        # Objective
        #
        def obj_rule(model):
            return 150 + pyo.quicksum(model.p[k] * model.x[k] for k in model.K)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

        def quad_obj_rule(model):
            return pyo.quicksum(model.x[k] ** 2 for k in model.K)

        self.model.quad_obj = pyo.Objective(rule=quad_obj_rule, sense=pyo.maximize)

        def nonlinear_obj_rule(model):
            return pyo.quicksum(pyo.cos(model.x[k]) for k in model.K)

        self.model.nonlinear_obj = pyo.Objective(
            rule=nonlinear_obj_rule, sense=pyo.maximize
        )

        self.model.obj.activate()
        self.model.quad_obj.deactivate()
        self.model.nonlinear_obj.deactivate()

        if quad_obj:
            self.model.obj.deactivate()
            self.model.quad_obj.activate()
            self.model.nonlinear_obj.deactivate()

        if nonlinear_obj:
            self.model.obj.deactivate()
            self.model.quad_obj.deactivate()
            self.model.nonlinear_obj.activate()
