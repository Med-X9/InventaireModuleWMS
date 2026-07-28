"""
Service métier pour EcartStockTheorique.

Sync depuis StockGapService + saisie / validation du résultat final.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from apps.inventory.exceptions import InventoryNotFoundError, InventoryValidationError
from apps.inventory.models import EcartStockTheorique, Inventory
from apps.inventory.repositories.ecart_stock_theorique_repository import (
    EcartStockTheoriqueRepository,
)
from apps.inventory.services.stock_gap_service import StockGapService
from apps.masterdata.models import Warehouse
from apps.users.models import UserApp

logger = logging.getLogger(__name__)


class EcartStockTheoriqueService:
    """Persistance et validation des écarts stock théorique vs pratique."""

    def __init__(
        self,
        repository: Optional[EcartStockTheoriqueRepository] = None,
        stock_gap_service: Optional[StockGapService] = None,
    ) -> None:
        self.repository = repository or EcartStockTheoriqueRepository()
        self.stock_gap_service = stock_gap_service or StockGapService()

    @staticmethod
    def default_resultat_final(qte_theorique: int, qte_pratique: int) -> Optional[int]:
        """
        Si théorique == pratique → résultat = pratique.
        Sinon → null (écart à traiter).
        """
        if int(qte_theorique) == int(qte_pratique):
            return int(qte_pratique)
        return None

    @transaction.atomic
    def sync_from_compute(
        self,
        inventory_id: int,
        warehouse_id: int,
        only_nonzero: bool = False,
    ) -> Dict[str, Any]:
        """
        Calcule les écarts puis upsert en base.

        - Lignes validées : quantités/ecart/designation non écrasés pour
          resultat_final / valide (les qté peuvent être rafraîchies sauf
          si valide — plan : ne touche pas resultat_final/valide si valide).
        - Création : applique default_resultat_final.
        - Non validée : met à jour qté ; recalcule resultat_final si null
          ou si égalité (pratique).
        """
        try:
            inventory = Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist as exc:
            raise InventoryNotFoundError(
                f"Inventaire {inventory_id} introuvable."
            ) from exc

        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist as exc:
            raise InventoryNotFoundError(
                f"Magasin {warehouse_id} introuvable."
            ) from exc

        # Inclure aussi écarts 0 pour préremplir resultat_final = pratique
        compute = self.stock_gap_service.compute_stock_gaps(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id,
            only_nonzero=only_nonzero,
        )

        existing = self.repository.bulk_get_existing_keys(inventory_id, warehouse_id)
        created = 0
        updated = 0
        skipped_validated = 0

        for line in compute["lignes"]:
            cle = line["cle"]
            mode = line["mode_groupement"]
            qte_theo = int(line["qte_theorique"])
            qte_prat = int(line["qte_inventoriee"])
            ecart = int(line["ecart"])
            designation = line.get("designation") or ""
            product_id = line.get("product_id")

            key = (cle, mode)
            row = existing.get(key)

            if row is None:
                self.repository.create(
                    inventory=inventory,
                    warehouse=warehouse,
                    article_cle=cle,
                    mode_groupement=mode,
                    designation=designation,
                    product_id=product_id,
                    qte_theorique=qte_theo,
                    qte_pratique=qte_prat,
                    ecart=ecart,
                    resultat_final=self.default_resultat_final(qte_theo, qte_prat),
                    valide=False,
                )
                created += 1
                continue

            if row.valide:
                # Ne pas toucher resultat_final / valide
                skipped_validated += 1
                continue

            qty_changed = (
                row.qte_theorique != qte_theo or row.qte_pratique != qte_prat
            )
            row.designation = designation
            if product_id is not None:
                row.product_id = product_id
            row.qte_theorique = qte_theo
            row.qte_pratique = qte_prat
            row.ecart = ecart

            # Recalcule resultat_final si null, ou si égalité (forcer pratique)
            if qte_theo == qte_prat:
                row.resultat_final = qte_prat
            elif row.resultat_final is None or (
                qty_changed and row.resultat_final is None
            ):
                row.resultat_final = self.default_resultat_final(qte_theo, qte_prat)

            self.repository.save(row)
            updated += 1

        return {
            "inventory_id": inventory_id,
            "warehouse_id": warehouse_id,
            "mode_groupement": compute["mode_groupement"],
            "is_variant": compute["is_variant"],
            "created": created,
            "updated": updated,
            "skipped_validated": skipped_validated,
            "total_compute_lines": len(compute["lignes"]),
            "totaux": compute["totaux"],
        }

    def list_for_warehouse(
        self, inventory_id: int, warehouse_id: int
    ) -> List[EcartStockTheorique]:
        return list(
            self.repository.get_for_inventory_warehouse(inventory_id, warehouse_id)
        )

    def get_queryset_for_warehouse(
        self, inventory_id: int, warehouse_id: int
    ):
        return self.repository.get_for_inventory_warehouse(
            inventory_id, warehouse_id
        )

    @transaction.atomic
    def update_resultat_final(
        self, ecart_id: int, resultat_final: int
    ) -> EcartStockTheorique:
        """Met à jour le résultat final — interdit si la ligne est validée."""
        row = self.repository.get_by_id(ecart_id)
        if row is None:
            raise InventoryNotFoundError(
                f"Écart stock théorique {ecart_id} introuvable."
            )
        if row.valide:
            raise InventoryValidationError(
                "Impossible de modifier le résultat final : la ligne est validée."
            )
        row.resultat_final = int(resultat_final)
        return self.repository.save(row)

    @transaction.atomic
    def valider(
        self, ecart_id: int, user: Optional[UserApp] = None
    ) -> EcartStockTheorique:
        """Valide la ligne (exige resultat_final non null)."""
        row = self.repository.get_by_id(ecart_id)
        if row is None:
            raise InventoryNotFoundError(
                f"Écart stock théorique {ecart_id} introuvable."
            )
        if row.valide:
            raise InventoryValidationError("Cette ligne est déjà validée.")
        if row.resultat_final is None:
            raise InventoryValidationError(
                "Le résultat final doit être renseigné avant validation."
            )
        row.valide = True
        row.validated_at = timezone.now()
        row.validated_by = user
        return self.repository.save(row)

    def valider_selection(
        self, ecart_ids: List[int], user: Optional[UserApp] = None
    ) -> Dict[str, Any]:
        """
        Valide une sélection de lignes (succès partiel autorisé).

        Body attendu côté API : { "ecart_ids": [1, 2, 3] }
        """
        if not ecart_ids:
            raise InventoryValidationError(
                "La liste ecart_ids est obligatoire et ne peut pas être vide."
            )

        seen = set()
        unique_ids: List[int] = []
        for eid in ecart_ids:
            if eid not in seen:
                seen.add(eid)
                unique_ids.append(eid)

        validated = []
        failed = []

        for ecart_id in unique_ids:
            try:
                row = self.valider(ecart_id, user=user)
                validated.append(
                    {
                        "id": row.id,
                        "article_cle": row.article_cle,
                        "resultat_final": row.resultat_final,
                        "valide": row.valide,
                    }
                )
            except (InventoryNotFoundError, InventoryValidationError) as exc:
                failed.append({"ecart_id": ecart_id, "error": str(exc)})

        return {
            "requested_count": len(unique_ids),
            "validated_count": len(validated),
            "failed_count": len(failed),
            "validated": validated,
            "failed": failed,
            "success": len(failed) == 0 and len(validated) > 0,
        }

    def assert_all_valides_for_close(
        self,
        inventory_id: int,
        warehouse_id: Optional[int] = None,
    ) -> None:
        """
        Lève InventoryValidationError s'il reste des lignes non validées.

        Utilisé pour clôture inventaire MAGASIN (tous magasins).
        """
        count = self.repository.count_non_valides(inventory_id, warehouse_id)
        if count == 0:
            return

        scope = (
            f"magasin {warehouse_id}"
            if warehouse_id is not None
            else "l'inventaire"
        )
        raise InventoryValidationError(
            f"Impossible de clôturer : {count} ligne(s) d'écart stock "
            f"non validée(s) pour {scope}."
        )
