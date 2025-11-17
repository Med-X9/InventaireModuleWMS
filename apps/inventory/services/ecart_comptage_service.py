from typing import Optional

from django.db import transaction

from ..models import EcartComptage
from ..repositories.ecart_comptage_repository import EcartComptageRepository
from ..exceptions import InventoryValidationError


class EcartComptageService:
    """
    Service métier pour la gestion des EcartComptage.
    """

    def __init__(self, repository: Optional[EcartComptageRepository] = None) -> None:
        self.repository = repository or EcartComptageRepository()

    @transaction.atomic
    def update_final_result(
        self,
        ecart_id: int,
        final_result: int,
        justification: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> EcartComptage:
        """
        Met à jour le résultat final d'un EcartComptage.

        Règles métier :
        - Il doit y avoir au moins deux comptages (séquences) enregistrés
          pour cet écart avant toute modification du résultat final.
        """
        ecart = self.repository.get_by_id(ecart_id)

        # Sécurité : on s'appuie sur total_sequences, mais on recalcule si besoin
        sequences_count = ecart.total_sequences or 0
        if sequences_count < 2:
            # Double check via la relation si jamais total_sequences n'est pas à jour
            sequences_count = ecart.counting_sequences.count()

        if sequences_count < 2:
            raise InventoryValidationError(
                "Il faut au moins deux comptages enregistrés pour modifier le résultat final."
            )

        ecart.final_result = final_result

        if justification is not None:
            ecart.justification = justification

        if resolved is not None:
            ecart.resolved = resolved
            if resolved and not ecart.stopped_reason:
                # Marquer explicitement que l'écart a été résolu manuellement
                ecart.stopped_reason = "RESOLU_MANUEL"

        return self.repository.save(ecart)

    @transaction.atomic
    def resolve_ecart(
        self,
        ecart_id: int,
        justification: Optional[str] = None,
    ) -> EcartComptage:
        """
        Marque un EcartComptage comme résolu (resolved = True).

        Règles métier :
        - Il doit y avoir au moins deux comptages (séquences) enregistrés.
        - Le champ final_result doit être renseigné (non nul).
        """
        ecart = self.repository.get_by_id(ecart_id)

        # Vérifier le nombre de séquences
        sequences_count = ecart.total_sequences or 0
        if sequences_count < 2:
            sequences_count = ecart.counting_sequences.count()

        if sequences_count < 2:
            raise InventoryValidationError(
                "Il faut au moins deux comptages enregistrés pour résoudre l'écart."
            )

        # Vérifier que le résultat final est renseigné
        if ecart.final_result is None:
            raise InventoryValidationError(
                "Le résultat final doit être renseigné avant de pouvoir résoudre l'écart."
            )

        ecart.resolved = True
        if justification is not None:
            ecart.justification = justification

        if not ecart.stopped_reason:
            ecart.stopped_reason = "RESOLU_MANUEL"

        return self.repository.save(ecart)

