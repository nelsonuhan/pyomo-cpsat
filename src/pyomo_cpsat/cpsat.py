import logging

from typing import Sequence, Dict, Optional, Mapping, List, Tuple

from pyomo.core.base.constraint import ConstraintData
from pyomo.core.base.var import VarData
from pyomo.core.base.param import ParamData
from pyomo.core.base.block import BlockData
from pyomo.core.base.objective import Objective, ObjectiveData
from pyomo.core.staleflag import StaleFlagManager

from pyomo.common.config import document_kwargs_from_configdict, ConfigValue
from pyomo.common.dependencies import attempt_import

from pyomo.contrib.solver.common.base import PersistentSolverBase, Availability
from pyomo.contrib.solver.common.config import PersistentSolverConfig
from pyomo.contrib.solver.common.results import Results

logger = logging.getLogger(__name__)

cpsat, cpsat_available = attempt_import('ortools.sat.python')


class Cpsat(PersistentSolverBase):
    """
    Interface to CP-SAT
    """

    CONFIG = PersistentSolverConfig()

    def __init__(self, **kwds) -> None:
        super().__init__(**kwds)
        self._active_config = self.config

    def available(self) -> Availability:
        if cpsat_available:
            return Availability.FullLicense
        else:
            return Availability.NotFound

    def version(self) -> Tuple:
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'version'."
        )

    @document_kwargs_from_configdict(CONFIG)
    def solve(self, model: BlockData, **kwargs) -> Results:
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'solve'."
        )

    def is_persistent(self) -> bool:
        return True

    def _load_vars(self, vars_to_load: Optional[Sequence[VarData]] = None) -> None:
        for var, val in self._get_primals(vars_to_load=vars_to_load).items():
            var.set_value(val, skip_validation=True)
        StaleFlagManager.mark_all_as_stale(delayed=True)

    def _get_primals(
        self, vars_to_load: Optional[Sequence[VarData]] = None
    ) -> Mapping[VarData, float]:
        raise NotImplementedError(
            f'{type(self)} does not support the get_primals method'
        )

    def _get_duals(
        self, cons_to_load: Optional[Sequence[ConstraintData]] = None
    ) -> Dict[ConstraintData, float]:
        raise NotImplementedError(f'{type(self)} does not support the get_duals method')

    def _get_reduced_costs(
        self, vars_to_load: Optional[Sequence[VarData]] = None
    ) -> Mapping[VarData, float]:
        raise NotImplementedError(
            f'{type(self)} does not support the get_reduced_costs method'
        )

    def set_instance(self, model: BlockData):
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'set_instance'."
        )

    def set_objective(self, obj: ObjectiveData):
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'set_objective'."
        )

    def add_variables(self, variables: List[VarData]):
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'add_variables'."
        )

    def add_parameters(self, params: List[ParamData]):
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'add_parameters'."
        )

    def add_constraints(self, cons: List[ConstraintData]):
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'add_constraints'."
        )

    def add_block(self, block: BlockData):
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'add_block'."
        )

    def remove_variables(self, variables: List[VarData]):
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'remove_variables'."
        )

    def remove_parameters(self, params: List[ParamData]):
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'remove_parameters'."
        )

    def remove_constraints(self, cons: List[ConstraintData]):
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'remove_constraints'."
        )

    def remove_block(self, block: BlockData):
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'remove_block'."
        )

    def update_variables(self, variables: List[VarData]):
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'update_variables'."
        )

    def update_parameters(self):
        raise NotImplementedError(
            f"Derived class {self.__class__.__name__} failed to implement required method 'update_parameters'."
        )
