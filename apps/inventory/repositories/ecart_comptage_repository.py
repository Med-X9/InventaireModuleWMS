from typing import List

from django.db import transaction
from django.db.models import Count, Q

from apps.inventory.exceptions.warehouse_exceptions import WarehouseNotFoundError
from apps.masterdata.models import Warehouse

from ..models import EcartComptage, CountingDetail, Inventory
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

    def get_unresolved_counting_details_by_inventory_and_warehouse(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> List[CountingDetail]:
        """
        Récupère les CountingDetail liés à des écarts de comptage non résolus
        pour un couple (inventaire, entrepôt).

        Règle métier :
        - On exclut les écarts dont le résultat final n'est pas nul ET résolus (= True).
        - On garde donc les détails liés à des EcartComptage où
          final_result est NULL ou resolved = False.
        """
        return list(
            CountingDetail.objects.filter(
                job__inventory_id=inventory_id,
                job__warehouse_id=warehouse_id,
                counting_sequences__ecart_comptage__inventory_id=inventory_id,
            )
            .filter(
                Q(counting_sequences__ecart_comptage__final_result__isnull=True)
                | Q(counting_sequences__ecart_comptage__resolved=False)
            )
            .select_related("job", "counting")
            .distinct()
        )

    def get_by_inventory_id(self, inventory_id: int) -> List[EcartComptage]:
        """
        Récupère tous les EcartComptage d'un inventaire.
        """
        return list(EcartComptage.objects.filter(inventory_id=inventory_id))

    def get_inventory_by_id(self, inventory_id: int) -> Inventory:
        """
        Récupère un inventaire par son ID.
        """
        try:
            return Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist as exc:
            raise InventoryNotFoundError(
                f"Inventaire avec l'ID {inventory_id} non trouvé."
            ) from exc

    def get_warehouse_by_id(self, warehouse_id: int) -> Warehouse:
        """
        Récupère un entrepôt / magasin par son ID.
        """
        try:
            return Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist as exc:
            raise WarehouseNotFoundError(
                f"Entrepôt avec l'ID {warehouse_id} non trouvé."
            ) from exc

    @transaction.atomic
    def bulk_resolve_ecarts_by_inventory_and_warehouse(
        self,
        inventory_id: int,
        warehouse_id: int,
        min_sequences: int,
    ) -> int:
        """
        Marque comme résolus les EcartComptage d'un inventaire / magasin qui :
        - ont un final_result non nul
        - ont au moins ``min_sequences`` ComptageSequence (selon type inventaire)

        Retourne le nombre d'écarts mis à jour.
        """
        eligible_ids = list(
            EcartComptage.objects.filter(
                inventory_id=inventory_id,
                final_result__isnull=False,
                counting_sequences__counting_detail__job__warehouse_id=warehouse_id,
            )
            .annotate(seq_count=Count("counting_sequences", distinct=True))
            .filter(seq_count__gte=min_sequences)
            .values_list("id", flat=True)
            .distinct()
        )
        if not eligible_ids:
            return 0
        return EcartComptage.objects.filter(id__in=eligible_ids).update(
            resolved=True,
            stopped_reason="RESOLU_MANUEL",
        )

    @transaction.atomic
    def bulk_resolve_ecarts_by_inventory(self, inventory_id: int) -> int:
        """
        Marque comme résolus (resolved = True) uniquement les EcartComptage d'un inventaire
        qui ont un final_result non nul.

        Retourne le nombre d'écarts mis à jour.
        """
        return EcartComptage.objects.filter(
            inventory_id=inventory_id,
            final_result__isnull=False,
        ).update(
            resolved=True,
            stopped_reason="RESOLU_MANUEL",
        )

