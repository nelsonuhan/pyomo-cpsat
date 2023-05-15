from pyomo.opt import SolverFactory

@SolverFactory.register('cpsat', doc='CP-SAT interface')
class CpsatInterface(object):
    def solve(self, model, **kwargs):
        print('Hello!')

    def available(self, exception_flag=True):
        return True

    def license_is_valid(self):
        return True

    def version(self):
        return (0, 0, 0)

    @property
    def options(self):
        pass

    @options.setter
    def options(self, val):
        pass
