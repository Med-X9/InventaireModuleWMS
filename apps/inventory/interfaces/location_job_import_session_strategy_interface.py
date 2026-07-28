"""
Interface Strategy : règles sessions pour import InventoryLocationJob.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ILocationJobImportSessionStrategy(ABC):
    """
    Contrat pour la validation des sessions selon le type d'inventaire.

    - GENERAL : session_1 + session_2 obligatoires (si active)
    - MAGASIN / TOURNANT : session_1 seule obligatoire (si active) ;
      session_2 optionnelle (colonne Excel et valeur)
    """

    @abstractmethod
    def required_columns(self) -> List[str]:
        """Colonnes Excel obligatoires."""
        raise NotImplementedError

    @abstractmethod
    def session_2_required(self) -> bool:
        """True si session_2 est obligatoire lorsque active=true."""
        raise NotImplementedError

    @abstractmethod
    def validate_cross_job_rules(
        self,
        validated_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Validations globales après les lignes (cohérence sessions / équipe unique).

        Returns:
            Liste d'erreurs (vide si OK).
        """
        raise NotImplementedError

    @abstractmethod
    def strategy_key(self) -> str:
        """Identifiant exposé (API / logs)."""
        raise NotImplementedError
