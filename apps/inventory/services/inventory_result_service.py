"""
Service pour le calcul des résultats d'inventaire par entrepôt et par comptage.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from ..exceptions import InventoryNotFoundError, InventoryValidationError
from ..models import Setting
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

        # Vérifier que l'entrepôt existe et est associé à cet inventaire
        from apps.masterdata.models import Warehouse
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id, is_deleted=False)
        except Warehouse.DoesNotExist:
            self.logger.warning(
                "Entrepôt introuvable lors du calcul des résultats "
                "(inventory_id=%s, warehouse_id=%s).",
                inventory_id,
                warehouse_id,
            )
            raise InventoryValidationError(
                f"Entrepôt introuvable (ID: {warehouse_id})."
            )
        
        # Vérifier que l'entrepôt est bien associé à cet inventaire
        if not Setting.objects.filter(inventory_id=inventory_id, warehouse_id=warehouse_id).exists():
            # Récupérer les entrepôts associés à cet inventaire pour un message plus utile
            associated_warehouses = Setting.objects.filter(
                inventory_id=inventory_id
            ).values_list('warehouse_id', flat=True)
            
            self.logger.warning(
                "L'entrepôt %s n'est pas associé à l'inventaire %s. Entrepôts associés: %s",
                warehouse_id,
                inventory_id,
                list(associated_warehouses),
            )
            raise InventoryValidationError(
                f"L'entrepôt {warehouse_id} ({warehouse.warehouse_name}) n'est pas associé à cet inventaire. "
                f"Entrepôts disponibles: {', '.join(map(str, associated_warehouses)) if associated_warehouses else 'Aucun'}."
            )

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

        self.logger.debug(f"📊 Nombre de lignes agrégées récupérées: {len(aggregated_rows)}")

        max_order_global = 0
        entries: Dict[Tuple[int, Optional[int], Optional[int]], Dict[str, Any]] = {}

        if not aggregated_rows:
            self.logger.warning(
                f"⚠️ Aucune donnée agrégée trouvée pour inventory_id={inventory_id}, warehouse_id={warehouse_id}"
            )
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
                        "reference": row.get("job_reference_alias"),
                    },
                    "product": None,
                    "quantities": {},
                    "assignment_statuses": {},  # Stocker le statut de l'assignment par ordre de comptage
                    "final_result": None,  # Stocker le final_result depuis EcartComptage
                    "ecart_id": row.get("ecart_id_alias"),
                    "resolved": None,  # Stocker le resolved depuis EcartComptage
                    "manual_result": None,  # Stocker le manual_result depuis EcartComptage
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
            # Stocker le statut de l'assignment pour cet ordre de comptage
            assignment_status = row.get("assignment_status_alias")
            if assignment_status:
                entry_data["assignment_statuses"][order] = assignment_status
            max_order_global = max(max_order_global, order)
            
            # Mettre à jour le final_result si disponible (sera le même pour tous les ordres)
            if row.get("final_result_agg") is not None:
                entry_data["final_result"] = row["final_result_agg"]
            
            # Mettre à jour le resolved si disponible (sera le même pour tous les ordres)
            # Convertir 0/1 en False/True car PostgreSQL retourne un entier après MAX(Cast(...))
            if row.get("resolved_agg") is not None:
                entry_data["resolved"] = bool(row["resolved_agg"])
            
            # Mettre à jour le manual_result si disponible (sera le même pour tous les ordres)
            # Convertir 0/1 en False/True car PostgreSQL retourne un entier après MAX(Cast(...))
            if row.get("manual_result_agg") is not None:
                entry_data["manual_result"] = bool(row["manual_result_agg"])

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
            assignment_statuses = entry.get("assignment_statuses", {})

            for order in range(1, max_order_global + 1):
                quantity = quantities.get(order)
                quantity_key = f"{order}er comptage"
                result_row[quantity_key] = quantity if quantity is not None else None
                
                # Ajouter le statut de l'assignment seulement pour les comptages 1 et 2
                if order in [1, 2]:
                    assignment_status = assignment_statuses.get(order)
                    status_key = f"statut_{order}er_comptage"
                    result_row[status_key] = assignment_status if assignment_status else None

                if previous_order is not None and previous_quantity is not None:
                    ecart_key = f"ecart_{previous_order}_{order}"
                    if quantity is None:
                        result_row[ecart_key] = None
                    else:
                        # Calculer l'écart
                        ecart_value = abs(quantity - previous_quantity)
                        
                        # Pour ecart_1_2 : afficher la valeur numérique
                        # Pour les autres écarts : afficher true (concordance) ou false (discordance)
                        if previous_order == 1 and order == 2:
                            result_row[ecart_key] = ecart_value
                        else:
                            result_row[ecart_key] = True if ecart_value == 0 else False
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
                result_row["result_id"] = entry["ecart_id"]  # Alias pour result_id
                # Ajouter le statut resolved depuis EcartComptage (booléen, peut être False ou None)
                result_row["resolved"] = entry.get("resolved")
                # Ajouter le statut manual_result depuis EcartComptage (booléen, peut être False ou None)
                result_row["manual_result"] = entry.get("manual_result")
            else:
                # Si pas d'ecart_id, result_id est None
                result_row["result_id"] = None
                result_row["manual_result"] = None

            formatted_results.append(result_row)

        return formatted_results

