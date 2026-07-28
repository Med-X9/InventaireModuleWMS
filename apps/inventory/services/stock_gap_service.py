"""
Service de calcul d'écart stock théorique vs inventorié.

Formule : ecart = qte_theorique - qte_inventoriee (signe conservé).
"""
from typing import Any, Dict, List, Optional

from apps.inventory.constants import StockGapGrouping
from apps.inventory.exceptions import InventoryNotFoundError
from apps.inventory.interfaces.theoretical_stock_provider import ITheoreticalStockProvider
from apps.inventory.providers.excel_theoretical_stock_provider import (
    ExcelTheoreticalStockProvider,
)
from apps.inventory.repositories.ecart_stock_theorique_repository import (
    EcartStockTheoriqueRepository,
)
from apps.inventory.repositories.stock_gap_repository import StockGapRepository


class StockGapService:
    """Consolide théorique et inventorié par Internal_Product_Code ou barcode."""

    def __init__(
        self,
        repository: Optional[StockGapRepository] = None,
        theoretical_provider: Optional[ITheoreticalStockProvider] = None,
        ecart_repository: Optional[EcartStockTheoriqueRepository] = None,
    ) -> None:
        self.repository = repository or StockGapRepository()
        self.theoretical_provider = (
            theoretical_provider or ExcelTheoreticalStockProvider()
        )
        self.ecart_repository = ecart_repository or EcartStockTheoriqueRepository()


    def compute_stock_gaps(
        self,
        inventory_id: int,
        warehouse_id: int,
        only_nonzero: bool = True,
    ) -> Dict[str, Any]:
        """
        Calcule les écarts pour un inventaire + magasin.

        Args:
            inventory_id: ID inventaire.
            warehouse_id: ID magasin.
            only_nonzero: Si True, exclut les lignes avec écart == 0.

        Returns:
            Dict avec mode_groupement, lignes, totaux.

        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas.
        """
        inventory = self.repository.get_inventory(inventory_id)
        if inventory is None:
            raise InventoryNotFoundError(f"Inventaire {inventory_id} introuvable.")

        is_variant = self.repository.get_is_variant(inventory_id)
        grouping_mode = (
            StockGapGrouping.BY_INTERNAL_CODE
            if is_variant
            else StockGapGrouping.BY_BARCODE
        )

        inventoried = self.repository.get_inventoried_quantities_by_product(
            inventory_id, warehouse_id
        )
        theoretical = self.theoretical_provider.get_quantities_by_product(
            inventory_id, warehouse_id
        )

        excluded = self.repository.get_excluded_product_ids()
        product_ids = set(inventoried.keys()) | set(theoretical.keys())
        product_ids -= excluded

        products_info = self.repository.get_products_info(list(product_ids))

        buckets: Dict[str, Dict[str, Any]] = {}
        for product_id in product_ids:
            info = products_info.get(product_id)
            if info is None:
                continue
            key = self._grouping_key(info, is_variant)
            if not key:
                continue
            if key not in buckets:
                buckets[key] = {
                    "cle": key,
                    "mode_groupement": grouping_mode,
                    "designation": info["designation"],
                    "product_id": product_id,
                    "qte_theorique": 0,
                    "qte_inventoriee": 0,
                }
            if info["designation"] and not buckets[key]["designation"]:
                buckets[key]["designation"] = info["designation"]

            buckets[key]["qte_theorique"] += int(theoretical.get(product_id, 0))
            buckets[key]["qte_inventoriee"] += int(inventoried.get(product_id, 0))

        lines: List[Dict[str, Any]] = []
        total_theo = 0
        total_inv = 0
        total_ecart = 0

        for bucket in buckets.values():
            ecart = bucket["qte_theorique"] - bucket["qte_inventoriee"]
            if only_nonzero and ecart == 0:
                continue
            line = {**bucket, "ecart": ecart}
            lines.append(line)
            total_theo += line["qte_theorique"]
            total_inv += line["qte_inventoriee"]
            total_ecart += ecart

        lines.sort(key=lambda row: row["cle"] or "")

        return {
            "inventory_id": inventory_id,
            "warehouse_id": warehouse_id,
            "mode_groupement": grouping_mode,
            "is_variant": is_variant,
            "lignes": lines,
            "totaux": {
                "qte_theorique": total_theo,
                "qte_inventoriee": total_inv,
                "ecart": total_ecart,
                "nombre_lignes": len(lines),
            },
        }

    def list_persisted_stock_gaps(
        self,
        inventory_id: int,
        warehouse_id: int,
        only_nonzero: bool = True,
    ) -> Dict[str, Any]:
        """
        Lit les écarts depuis EcartStockTheorique (après ANALYSER).

        Ne recalcule pas. Expose resultat_final + valide.
        Pas de mode de regroupement dans la réponse API.
        """
        inventory = self.repository.get_inventory(inventory_id)
        if inventory is None:
            raise InventoryNotFoundError(f"Inventaire {inventory_id} introuvable.")

        qs = self.ecart_repository.get_for_inventory_warehouse(
            inventory_id, warehouse_id
        )
        if only_nonzero:
            qs = qs.exclude(ecart=0)

        lines: List[Dict[str, Any]] = []
        total_theo = 0
        total_inv = 0
        total_ecart = 0
        nb_valides = 0

        for row in qs:
            line = {
                "ecart_id": row.id,
                "cle": row.article_cle,
                "designation": row.designation or "",
                "qte_theorique": int(row.qte_theorique),
                "qte_inventoriee": int(row.qte_pratique),
                "ecart": int(row.ecart),
                "resultat_final": row.resultat_final,
                "valide": bool(row.valide),
            }
            lines.append(line)
            total_theo += line["qte_theorique"]
            total_inv += line["qte_inventoriee"]
            total_ecart += line["ecart"]
            if row.valide:
                nb_valides += 1

        return {
            "inventory_id": inventory_id,
            "warehouse_id": warehouse_id,
            "source": "ecart_stock_theorique",
            "lignes": lines,
            "totaux": {
                "qte_theorique": total_theo,
                "qte_inventoriee": total_inv,
                "ecart": total_ecart,
                "nombre_lignes": len(lines),
                "nombre_valides": nb_valides,
            },
        }

    @staticmethod
    def _grouping_key(info: Dict[str, Any], is_variant: bool) -> str:
        """Clé : Internal_Product_Code (variante) ou barcode."""
        if is_variant:
            return info.get("internal_code") or ""
        return info.get("barcode") or ""
