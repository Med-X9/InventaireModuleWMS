"""
Repository pour l'agrégation inventoriée / métadonnées écart stock théorique.
"""
from typing import Dict, List, Optional, Set

from django.db.models import Max, Sum

from apps.inventory.constants import StockGapGrouping
from apps.inventory.models import ComptageSequence, Counting, CountingDetail, EcartComptage, Inventory
from apps.masterdata.models import Product


class StockGapRepository:
    """Accès données pour le calcul d'écart stock théorique vs inventorié."""

    def get_inventory(self, inventory_id: int) -> Optional[Inventory]:
        """Retourne l'inventaire ou None."""
        try:
            return Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            return None

    def get_is_variant(self, inventory_id: int) -> bool:
        """
        Lit Counting.is_variant du premier comptage de l'inventaire.

        Returns:
            False si aucun comptage.
        """
        counting = (
            Counting.objects.filter(inventory_id=inventory_id)
            .order_by("order", "id")
            .first()
        )
        if counting is None:
            return False
        return bool(counting.is_variant)

    def get_excluded_product_ids(self) -> Set[int]:
        """IDs produits test exclus de la consolidation."""
        return set(
            Product.objects.filter(
                Internal_Product_Code=StockGapGrouping.EXCLUDED_INTERNAL_CODE
            ).values_list("id", flat=True)
        )

    def get_inventoried_quantities_by_product(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> Dict[int, int]:
        """
        Quantité inventoriée (pratique) par produit pour un magasin.

        Règles :
        - Filtre magasin via ``CountingDetail.job.warehouse_id`` (MAGASIN
          sans emplacement stock, emplacements job locaux).
        - Si ``EcartComptage.final_result`` est renseigné → on l'utilise
          (consensus / résolution multi-comptages).
        - Sinon → quantité de la dernière séquence de l'écart.
        - CountingDetail orphelins (sans écart) : somme de
          ``quantity_inventoried``.

        Les articles inventoriés absents du stock théorique apparaissent
        via cette map (union côté StockGapService).
        """
        product_sums: Dict[int, int] = {}
        covered_detail_ids: Set[int] = set()

        # Écarts ayant au moins une séquence sur ce magasin
        ecart_ids = (
            EcartComptage.objects.filter(
                inventory_id=inventory_id,
                counting_sequences__counting_detail__job__warehouse_id=warehouse_id,
            )
            .values_list("id", flat=True)
            .distinct()
        )

        ecarts = EcartComptage.objects.filter(id__in=ecart_ids).only(
            "id", "final_result"
        )

        # Dernière séquence + produit par écart (magasin)
        last_seq_rows = (
            ComptageSequence.objects.filter(
                ecart_comptage_id__in=ecart_ids,
                counting_detail__job__warehouse_id=warehouse_id,
            )
            .values("ecart_comptage_id")
            .annotate(max_seq=Max("sequence_number"))
        )
        max_seq_by_ecart = {
            int(row["ecart_comptage_id"]): int(row["max_seq"])
            for row in last_seq_rows
        }

        last_sequences = ComptageSequence.objects.filter(
            ecart_comptage_id__in=ecart_ids,
            counting_detail__job__warehouse_id=warehouse_id,
        ).select_related("counting_detail")

        seq_by_ecart: Dict[int, ComptageSequence] = {}
        for seq in last_sequences:
            expected = max_seq_by_ecart.get(seq.ecart_comptage_id)
            if expected is None or seq.sequence_number != expected:
                continue
            # Une seule séquence "dernière" par écart
            if seq.ecart_comptage_id not in seq_by_ecart:
                seq_by_ecart[seq.ecart_comptage_id] = seq

        for ecart in ecarts:
            seq = seq_by_ecart.get(ecart.id)
            if seq is None or seq.counting_detail_id is None:
                continue
            detail = seq.counting_detail
            product_id = detail.product_id
            if product_id is None:
                continue
            covered_detail_ids.add(detail.id)

            # MAGASIN/TOURNANT : final_result renseigné dès le 1er comptage
            # GENERAL : final_result = consensus multi-comptages
            if ecart.final_result is not None:
                qty = int(ecart.final_result)
            else:
                qty = int(seq.quantity)

            product_sums[product_id] = product_sums.get(product_id, 0) + qty

        # Détails inventoriés sans EcartComptage (ou hors séquences)
        orphan_rows = (
            CountingDetail.objects.filter(
                job__inventory_id=inventory_id,
                job__warehouse_id=warehouse_id,
                product_id__isnull=False,
            )
            .exclude(id__in=covered_detail_ids)
            .values("product_id")
            .annotate(total=Sum("quantity_inventoried"))
        )
        for row in orphan_rows:
            product_id = row["product_id"]
            if product_id is None:
                continue
            product_sums[int(product_id)] = product_sums.get(
                int(product_id), 0
            ) + int(row["total"] or 0)

        return product_sums

    def get_products_info(self, product_ids: List[int]) -> Dict[int, Dict]:
        """Métadonnées produits pour construire la clé de groupement."""
        if not product_ids:
            return {}
        products = Product.objects.filter(id__in=product_ids)
        result: Dict[int, Dict] = {}
        for product in products:
            result[product.id] = {
                "product_id": product.id,
                "reference": product.reference or "",
                "barcode": product.Barcode or "",
                "designation": product.Short_Description or "",
                "internal_code": product.Internal_Product_Code or "",
            }
        return result
