"""
Repository pour EcartStockTheorique.
"""
from typing import List, Optional

from django.db.models import QuerySet

from apps.inventory.models import EcartStockTheorique


class EcartStockTheoriqueRepository:
    """Accès ORM pour les écarts stock théorique / pratique."""

    def get_by_id(self, ecart_id: int) -> Optional[EcartStockTheorique]:
        try:
            return EcartStockTheorique.objects.select_related(
                "inventory", "warehouse", "product", "validated_by"
            ).get(id=ecart_id)
        except EcartStockTheorique.DoesNotExist:
            return None

    def get_for_inventory_warehouse(
        self, inventory_id: int, warehouse_id: int
    ) -> QuerySet:
        return (
            EcartStockTheorique.objects.filter(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id,
            )
            .select_related("product", "validated_by", "warehouse")
            .order_by("article_cle", "id")
        )

    def get_by_unique_key(
        self,
        inventory_id: int,
        warehouse_id: int,
        article_cle: str,
        mode_groupement: str,
    ) -> Optional[EcartStockTheorique]:
        try:
            return EcartStockTheorique.objects.get(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id,
                article_cle=article_cle,
                mode_groupement=mode_groupement,
            )
        except EcartStockTheorique.DoesNotExist:
            return None

    def create(self, **kwargs) -> EcartStockTheorique:
        instance = EcartStockTheorique(**kwargs)
        if not instance.reference:
            instance.reference = instance.generate_reference(
                EcartStockTheorique.REFERENCE_PREFIX
            )
        instance.save()
        return instance

    def save(self, instance: EcartStockTheorique) -> EcartStockTheorique:
        instance.save()
        return instance

    def bulk_get_existing_keys(
        self, inventory_id: int, warehouse_id: int
    ) -> dict:
        """Map (article_cle, mode_groupement) -> instance."""
        rows = EcartStockTheorique.objects.filter(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id,
        )
        return {(row.article_cle, row.mode_groupement): row for row in rows}

    def get_nonzero_ecarts(
        self, inventory_id: int, warehouse_id: int
    ) -> QuerySet:
        """Lignes d'analyse avec écart ≠ 0 pour inventaire + magasin."""
        return (
            self.get_for_inventory_warehouse(inventory_id, warehouse_id)
            .exclude(ecart=0)
            .select_related("product", "warehouse")
        )

    def get_non_valides(
        self,
        inventory_id: int,
        warehouse_id: Optional[int] = None,
    ) -> QuerySet:
        """Lignes non validées pour un inventaire (et magasin optionnel)."""
        qs = EcartStockTheorique.objects.filter(
            inventory_id=inventory_id,
            valide=False,
        )
        if warehouse_id is not None:
            qs = qs.filter(warehouse_id=warehouse_id)
        return qs.select_related("warehouse").order_by("article_cle", "id")

    def count_non_valides(
        self,
        inventory_id: int,
        warehouse_id: Optional[int] = None,
    ) -> int:
        return self.get_non_valides(inventory_id, warehouse_id).count()

    def get_by_ids(self, ecart_ids: List[int]) -> QuerySet:
        return EcartStockTheorique.objects.filter(id__in=ecart_ids).select_related(
            "inventory", "warehouse", "product", "validated_by"
        )
