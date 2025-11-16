from typing import Any

from django.db import transaction

from ..models import EcartComptage
from ..exceptions import InventoryNotFoundError


class EcartComptageRepository:
    """
    Repository pour la gestion des EcartComptage.
    Contient uniquement la logique d'accès aux données (ORM).
    """

    def get_by_id(self, ecart_id: int) -> EcartComptage:
        """
        Récupère un EcartComptage par son ID.
        """
        try:
            return EcartComptage.objects.get(id=ecart_id)
        except EcartComptage.DoesNotExist as exc:
            raise InventoryNotFoundError(
                f"EcartComptage avec l'ID {ecart_id} non trouvé."
            ) from exc

    @transaction.atomic
    def save(self, ecart: EcartComptage) -> EcartComptage:
        """
        Sauvegarde un EcartComptage et le retourne.
        """
        ecart.save()
        return ecart


