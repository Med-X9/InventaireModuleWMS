"""
Interface Strategy pour le calcul de EcartComptage.final_result.
"""
from abc import ABC, abstractmethod
from typing import List, Optional


class IEcartFinalResultStrategy(ABC):
    """
    Contrat pour déterminer final_result selon le type d'inventaire.

    - GENERAL : consensus multi-comptages (logique historique)
    - MAGASIN / TOURNANT : résultat = dernière quantité comptée
    """

    @abstractmethod
    def resolve_final_result(
        self,
        quantities: List[int],
        current_result: Optional[int],
    ) -> Optional[int]:
        """
        Calcule la valeur à stocker dans EcartComptage.final_result.

        Args:
            quantities: Quantités des séquences triées par numéro (1er → N).
            current_result: final_result actuel (peut être None).

        Returns:
            Valeur de final_result, ou None si pas encore déterminable.
        """
        raise NotImplementedError
