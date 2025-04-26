import pyomo.environ as pyo


class SimpleModel:
    """
    A simple resource allocation model with 3 products and 2 resources.
    """

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
        self.model.x = pyo.Var(self.model.K, domain=pyo.Integers, bounds=(0, 100))

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
            return model.total_cakes >= 4

        self.model.total_cakes_con = pyo.Constraint(rule=total_cakes_rule)

        #
        # Objective
        #
        def obj_rule(model):
            return 150 + pyo.quicksum(model.p[k] * model.x[k] for k in model.K)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)


class MaxObjModel:
    """
    A model with a maximization objective.
    """

    def __init__(self):
        self.model = pyo.ConcreteModel()

        self.model.I = pyo.Set(initialize=[1, 2, 3])
        self.model.w = pyo.Param(self.model.I, initialize={1: 10, 2: 20, 3: 30})
        self.model.x = pyo.Var(self.model.I, domain=pyo.Integers, bounds=(0, 100))

        def con_rule(model):
            return pyo.quicksum(model.w[i] * model.x[i] for i in model.I) <= 20

        self.model.con = pyo.Constraint(rule=con_rule)

        def obj_rule(model):
            return pyo.quicksum(model.x[i] for i in model.I)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)


class MinObjModel:
    """
    A model with a minimization objective.
    """

    def __init__(self):
        self.model = pyo.ConcreteModel()

        self.model.I = pyo.Set(initialize=[1, 2, 3])
        self.model.w = pyo.Param(self.model.I, initialize={1: 10, 2: 20, 3: 30})
        self.model.x = pyo.Var(self.model.I, domain=pyo.Integers, bounds=(0, 100))

        def con_rule(model):
            return pyo.quicksum(model.w[i] * model.x[i] for i in model.I) <= 20

        self.model.con = pyo.Constraint(rule=con_rule)

        def obj_rule(model):
            return pyo.quicksum(model.x[i] for i in model.I)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)


class RealVarsModel:
    """
    A model with real variables.
    """

    def __init__(self):
        self.model = pyo.ConcreteModel()

        self.model.I = pyo.Set(initialize=[1, 2, 3])
        self.model.w = pyo.Param(self.model.I, initialize={1: 10, 2: 20, 3: 30})
        self.model.x = pyo.Var(self.model.I, domain=pyo.Reals, bounds=(0, 100))

        def con_rule(model):
            return pyo.quicksum(model.w[i] * model.x[i] for i in model.I) <= 20

        self.model.con = pyo.Constraint(rule=con_rule)

        def obj_rule(model):
            return pyo.quicksum(model.x[i] for i in model.I)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)


class NoLbVarsModel:
    """
    A model with variables unbounded from below.
    """

    def __init__(self):
        self.model = pyo.ConcreteModel()

        self.model.I = pyo.Set(initialize=[1, 2, 3])
        self.model.w = pyo.Param(self.model.I, initialize={1: 10, 2: 20, 3: 30})
        self.model.x = pyo.Var(self.model.I, domain=pyo.Integers, bounds=(None, 100))

        def con_rule(model):
            return pyo.quicksum(model.w[i] * model.x[i] for i in model.I) <= 20

        self.model.con = pyo.Constraint(rule=con_rule)

        def obj_rule(model):
            return pyo.quicksum(model.x[i] for i in model.I)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)


class NoUbVarsModel:
    """
    A model with variables unbounded from above.
    """

    def __init__(self):
        self.model = pyo.ConcreteModel()

        self.model.I = pyo.Set(initialize=[1, 2, 3])
        self.model.w = pyo.Param(self.model.I, initialize={1: 10, 2: 20, 3: 30})
        self.model.x = pyo.Var(self.model.I, domain=pyo.Integers, bounds=(0, None))

        def con_rule(model):
            return pyo.quicksum(model.w[i] * model.x[i] for i in model.I) <= 20

        self.model.con = pyo.Constraint(rule=con_rule)

        def obj_rule(model):
            return pyo.quicksum(model.x[i] for i in model.I)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)


class QuadConModel:
    """
    A model with a quadratic constraint.
    """

    def __init__(self):
        self.model = pyo.ConcreteModel()

        self.model.I = pyo.Set(initialize=[1, 2, 3])
        self.model.w = pyo.Param(self.model.I, initialize={1: 10, 2: 20, 3: 30})
        self.model.x = pyo.Var(self.model.I, domain=pyo.Integers, bounds=(0, 100))

        def con_rule(model):
            return pyo.quicksum(model.w[i] * model.x[i] ** 3 for i in model.I) <= 20

        self.model.con = pyo.Constraint(rule=con_rule)

        def obj_rule(model):
            return pyo.quicksum(model.x[i] for i in model.I)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)


class NonlinearConModel:
    """
    A model with a nonlinear (but not quadratic) constraint.
    """

    def __init__(self):
        self.model = pyo.ConcreteModel()

        self.model.I = pyo.Set(initialize=[1, 2, 3])
        self.model.w = pyo.Param(self.model.I, initialize={1: 10, 2: 20, 3: 30})
        self.model.x = pyo.Var(self.model.I, domain=pyo.Integers, bounds=(0, 100))

        def con_rule(model):
            return pyo.quicksum(model.w[i] * pyo.sin(model.x[i]) for i in model.I) <= 20

        self.model.con = pyo.Constraint(rule=con_rule)

        def obj_rule(model):
            return pyo.quicksum(model.x[i] for i in model.I)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)


class QuadObjModel:
    """
    A model with a quadratic objective.
    """

    def __init__(self):
        self.model = pyo.ConcreteModel()

        self.model.I = pyo.Set(initialize=[1, 2, 3])
        self.model.w = pyo.Param(self.model.I, initialize={1: 10, 2: 20, 3: 30})
        self.model.x = pyo.Var(self.model.I, domain=pyo.Integers, bounds=(0, 100))

        def con_rule(model):
            return pyo.quicksum(model.w[i] * model.x[i] for i in model.I) <= 20

        self.model.con = pyo.Constraint(rule=con_rule)

        def obj_rule(model):
            return pyo.quicksum(model.x[i] ** 2 for i in model.I)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)


class NonlinearObjModel:
    """
    A model with a nonlinear (but not quadratic) objective.
    """

    def __init__(self):
        self.model = pyo.ConcreteModel()

        self.model.I = pyo.Set(initialize=[1, 2, 3])
        self.model.w = pyo.Param(self.model.I, initialize={1: 10, 2: 20, 3: 30})
        self.model.x = pyo.Var(self.model.I, domain=pyo.Integers, bounds=(0, 100))

        def con_rule(model):
            return pyo.quicksum(model.w[i] * model.x[i] for i in model.I) <= 20

        self.model.con = pyo.Constraint(rule=con_rule)

        def obj_rule(model):
            return pyo.quicksum(pyo.cos(model.x[i]) for i in model.I)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)


class InfeasibleModel:
    """
    An infeasible model.
    """

    def __init__(self):
        self.model = pyo.ConcreteModel()

        self.model.I = pyo.Set(initialize=[1, 2, 3])
        self.model.w = pyo.Param(self.model.I, initialize={1: 10, 2: 20, 3: 30})
        self.model.x = pyo.Var(self.model.I, domain=pyo.Integers, bounds=(10, 100))

        def infeasible_con_rule(model):
            return pyo.quicksum(model.w[i] * model.x[i] for i in model.I) <= 20

        self.model.infeasible_con = pyo.Constraint(rule=infeasible_con_rule)

        def obj_rule(model):
            return pyo.quicksum(model.x[i] for i in model.I)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)


class InactiveConModel:
    """
    A model with an inactive constraint.
    """

    def __init__(self):
        self.model = pyo.ConcreteModel()

        self.model.I = pyo.Set(initialize=[1, 2, 3])
        self.model.w = pyo.Param(self.model.I, initialize={1: 10, 2: 20, 3: 30})
        self.model.x = pyo.Var(self.model.I, domain=pyo.Integers, bounds=(0, 100))

        def con_rule(model):
            return pyo.quicksum(model.w[i] * model.x[i] for i in model.I) <= 20

        self.model.con = pyo.Constraint(rule=con_rule)

        def inactive_con_rule(model):
            return pyo.quicksum(model.w[i] * model.x[i] for i in model.I) >= 100

        self.model.inactive_con = pyo.Constraint(rule=inactive_con_rule)
        self.model.inactive_con.deactivate()

        def obj_rule(model):
            return pyo.quicksum(model.x[i] for i in model.I)

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)


class ConstantObjModel:
    """
    A model with a constant objective.
    """

    def __init__(self):
        self.model = pyo.ConcreteModel()

        self.model.I = pyo.Set(initialize=[1, 2, 3])
        self.model.w = pyo.Param(self.model.I, initialize={1: 10, 2: 20, 3: 30})
        self.model.x = pyo.Var(self.model.I, domain=pyo.Integers, bounds=(0, 100))

        def con_rule(model):
            return pyo.quicksum(model.w[i] * model.x[i] for i in model.I) <= 10

        self.model.con = pyo.Constraint(rule=con_rule)

        def obj_rule(model):
            return 500 + 0 * model.x[1]

        self.model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)
