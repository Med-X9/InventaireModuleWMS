"""
Service pour le calcul des résultats d'inventaire par entrepôt et par comptage.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from ..exceptions import InventoryNotFoundError, InventoryValidationError
from ..repositories import (
    CountingRepository,
    InventoryRepository,
    WarehouseRepository,
)


class InventoryResultService:
    """
    Service responsable de l'agrégation des résultats de comptage par entrepôt.
    """

    def __init__(
        self,
        counting_repository: Optional[CountingRepository] = None,
        inventory_repository: Optional[InventoryRepository] = None,
        warehouse_repository: Optional[WarehouseRepository] = None,
    ) -> None:
        self.counting_repository = counting_repository or CountingRepository()
        self.inventory_repository = inventory_repository or InventoryRepository()
        self.warehouse_repository = warehouse_repository or WarehouseRepository()
        self.logger = logging.getLogger(__name__)

    def get_inventory_results_for_warehouse(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Calcule les résultats d'un inventaire pour un entrepôt spécifique.

        Args:
            inventory_id: Identifiant de l'inventaire cible.
            warehouse_id: Identifiant de l'entrepôt cible.

        Returns:
            Liste de dictionnaires formatés selon la spécification métier.
        """
        # Vérification de l'existence de l'inventaire et de l'entrepôt.
        try:
            self.inventory_repository.get_by_id(inventory_id)
        except InventoryNotFoundError as exc:
            self.logger.warning(
                "Inventaire introuvable lors du calcul des résultats (id=%s).",
                inventory_id,
            )
            raise exc

        warehouse = self.warehouse_repository.get_by_id(warehouse_id)
        if warehouse is None:
            self.logger.warning(
                "Entrepôt introuvable lors du calcul des résultats "
                "(inventory_id=%s, warehouse_id=%s).",
                inventory_id,
                warehouse_id,
            )
            raise InventoryValidationError("Entrepôt introuvable.")

        countings = self.counting_repository.get_by_inventory_id(inventory_id)
        if not countings:
            raise InventoryValidationError(
                "Aucun comptage n'est configuré pour cet inventaire."
            )

        # Déterminer le mode de comptage appliqué à l'inventaire.
        modes = {
            (counting.count_mode or "").strip().lower()
            for counting in countings
            if counting.count_mode
        }

        if not modes:
            raise InventoryValidationError(
                "Impossible de déterminer le mode de comptage pour cet inventaire."
            )

        supported_modes = {"par article", "en vrac"}
        unsupported_modes = modes - supported_modes
        if unsupported_modes:
            raise InventoryValidationError(
                "Modes de comptage non supportés pour l'agrégation: "
                f"{', '.join(sorted(unsupported_modes))}."
            )

        if len(modes) > 1:
            raise InventoryValidationError(
                "L'agrégation des résultats nécessite un mode de comptage unique "
                "pour tout l'inventaire."
            )

        mode = modes.pop()

        aggregated_rows = self.counting_repository.get_inventory_results_by_warehouse(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id,
        )

        max_order_global = 0
        entries: Dict[Tuple[int, Optional[int], Optional[int]], Dict[str, Any]] = {}

        if not aggregated_rows:
            return []

        for row in aggregated_rows:
            entry_key: Tuple[int, Optional[int], Optional[int]] = (
                row["location_id"],
                row.get("product_id"),
                row.get("job_id"),
            )

            entry_data = entries.setdefault(
                entry_key,
                {
                    "location": {
                        "id": row["location_id"],
                        "reference": row["location_reference_alias"],
                        "code": row["location_code_alias"],
                    },
                    "job": {
                        "id": row.get("job_id"),
                    },
                    "product": None,
                    "quantities": {},
                    "final_result": None,  # Stocker le final_result depuis EcartComptage
                    "ecart_id": row.get("ecart_id_alias"),
                    "resolved": None,  # Stocker le resolved depuis EcartComptage
                },
            )

            if row.get("product_id"):
                entry_data["product"] = {
                    "reference": row["product_reference_alias"],
                    "barcode": row.get("product_barcode_alias"),
                    "description": row.get("product_description_alias"),
                    "internal_code": row.get("product_internal_code_alias"),
                }

            order = row["counting_order_alias"]
            quantity = row["total_quantity"] or 0
            entry_data["quantities"][order] = quantity
            max_order_global = max(max_order_global, order)
            
            # Mettre à jour le final_result si disponible (sera le même pour tous les ordres)
            if row.get("final_result_agg") is not None:
                entry_data["final_result"] = row["final_result_agg"]
            
            # Mettre à jour le resolved si disponible (sera le même pour tous les ordres)
            if row.get("resolved_agg") is not None:
                entry_data["resolved"] = row["resolved_agg"]

        formatted_results: List[Dict[str, Any]] = []

        for entry in sorted(
            entries.values(),
            key=lambda item: (
                item["location"]["reference"] or "",
                item["product"]["reference"] if item["product"] else "",
                item["job"]["id"] or 0,
            ),
        ):
            quantities = entry["quantities"]
            if not quantities:
                continue

            result_row: Dict[str, Any] = {
                "location": entry["location"]["reference"] or "",
                "location_id": entry["location"]["id"],
            }

            if mode == "par article" and entry["product"]:
                # Utiliser le code-barres du produit, ou la référence en fallback
                result_row["product"] = entry["product"].get("barcode") or entry["product"].get("reference") or ""
                # Ajouter la désignation du produit si disponible
                if entry["product"].get("description"):
                    result_row["product_description"] = entry["product"]["description"]
                # Ajouter le code interne du produit si disponible
                if entry["product"].get("internal_code"):
                    result_row["product_internal_code"] = entry["product"]["internal_code"]

            job_info = entry.get("job")
            if job_info and job_info.get("id") is not None:
                result_row["job_id"] = job_info["id"]
                job_reference = job_info.get("reference")
                if job_reference:
                    result_row["job_reference"] = job_reference

            previous_order: Optional[int] = None
            previous_quantity: Optional[int] = None

            for order in range(1, max_order_global + 1):
                quantity = quantities.get(order)
                quantity_key = f"{order}er comptage"
                result_row[quantity_key] = quantity if quantity is not None else None

                if previous_order is not None and previous_quantity is not None:
                    ecart_key = f"ecart_{previous_order}_{order}"
                    if quantity is None:
                        result_row[ecart_key] = None
                    else:
                        # Utiliser la valeur absolue pour éviter les écarts négatifs
                        result_row[ecart_key] = abs(quantity - previous_quantity)
                elif previous_order is not None:
                    ecart_key = f"ecart_{previous_order}_{order}"
                    result_row[ecart_key] = None

                previous_order = order
                previous_quantity = quantity

            # Utiliser le final_result depuis EcartComptage
            # Si null, rester null (pas de fallback)
            result_row["final_result"] = entry.get("final_result")

            # Ajouter l'identifiant d'EcartComptage si disponible
            if entry.get("ecart_id") is not None:
                result_row["ecart_comptage_id"] = entry["ecart_id"]
                # Ajouter le statut resolved depuis EcartComptage (booléen, peut être False ou None)
                result_row["resolved"] = entry.get("resolved")

            formatted_results.append(result_row)

        return formatted_results

