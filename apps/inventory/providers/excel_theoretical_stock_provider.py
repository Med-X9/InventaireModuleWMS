"""
Provider stock théorique V1 : données issues de l'import Excel (masterdata.Stock).
"""
from typing import Dict

from django.db.models import Sum

from apps.inventory.interfaces.theoretical_stock_provider import ITheoreticalStockProvider
from apps.masterdata.models import Stock


class ExcelTheoreticalStockProvider(ITheoreticalStockProvider):
    """Agrège Stock.quantity_available pour inventory + warehouse."""

    def get_quantities_by_product(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> Dict[int, int]:
        rows = (
            Stock.objects.filter(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id,
                product_id__isnull=False,
            )
            .values("product_id")
            .annotate(total=Sum("quantity_available"))
        )
        return {
            int(row["product_id"]): int(row["total"] or 0)
            for row in rows
            if row["product_id"] is not None
        }


class WmsTheoreticalStockProvider(ITheoreticalStockProvider):
    """Stub phase 2 — connecteur API WMS non implémenté en V1."""

    def get_quantities_by_product(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> Dict[int, int]:
        raise NotImplementedError(
            "Le provider stock théorique WMS n'est pas encore implémenté."
        )
