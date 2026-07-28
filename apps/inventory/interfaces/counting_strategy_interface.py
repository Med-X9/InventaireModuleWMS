"""
Interface Strategy pour les modes de comptage.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

from apps.inventory.models import Counting


class ICountingStrategy(ABC):
    """
    Contrat commun pour les stratégies de création/validation de comptage.

    Chaque mode (en vrac, par article, image de stock) fournit une
    implémentation interchangeable sélectionnée à l'exécution.
    """

    @abstractmethod
    def validate_counting_data(self, data: Dict[str, Any]) -> None:
        """
        Valide les données du comptage sans créer l'objet.

        Args:
            data: Données du comptage à valider.

        Raises:
            CountingValidationError: Si les données sont invalides.
        """
        raise NotImplementedError

    @abstractmethod
    def create_counting(self, data: Dict[str, Any]) -> Counting:
        """
        Valide puis crée un comptage selon les règles du mode.

        Args:
            data: Données du comptage (doit contenir inventory_id, order, count_mode…).

        Returns:
            Counting: Instance créée et persistée.

        Raises:
            CountingValidationError: Si les données sont invalides.
        """
        raise NotImplementedError
