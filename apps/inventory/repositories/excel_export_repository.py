"""
Repository pour les opérations de données pour l'export Excel consolidé
"""
from typing import Any, Dict, List, Optional, Tuple

from apps.masterdata.models import Product, Warehouse

from ..models import Counting, EcartComptage, Inventory


class ExcelExportRepository:
    """Repository pour l'export Excel consolidé par article"""
    
    def get_inventory_by_id(self, inventory_id: int) -> Optional[Inventory]:
        """Récupère un inventaire par ID"""
        try:
            return Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            return None

    def get_warehouse_by_id(self, warehouse_id: int) -> Optional[Warehouse]:
        """Récupère un magasin par ID."""
        try:
            return Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist:
            return None
    
    def get_counting_by_order(self, inventory_id: int, order: int) -> Optional[Counting]:
        """Récupère un comptage par inventaire et ordre."""
        return Counting.objects.filter(
            inventory_id=inventory_id,
            order=order,
        ).first()

    def get_countings_orders_2_and_3(
        self,
        inventory_id: int,
    ) -> Tuple[Optional[Counting], Optional[Counting]]:
        """Récupère les comptages d'ordre 2 et 3 (accès données uniquement)."""
        return (
            self.get_counting_by_order(inventory_id, 2),
            self.get_counting_by_order(inventory_id, 3),
        )

    def get_ecarts_resolution_counts(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> Tuple[int, int]:
        """Retourne (total, résolus) pour l'inventaire et le magasin."""
        ecarts = EcartComptage.objects.filter(
            inventory_id=inventory_id,
            counting_sequences__counting_detail__job__warehouse_id=warehouse_id,
        ).distinct()
        return ecarts.count(), ecarts.filter(resolved=True).count()
    
    def get_consolidated_data_by_inventory_and_warehouse(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Récupère les données consolidées par article pour un inventaire / magasin.

        Utilise UNIQUEMENT le final_result des EcartComptage RÉSOLUS.

        Pour chaque produit apparaissant dans des EcartComptage résolus,
        la quantité consolidée est la SOMME des final_result de TOUS les EcartComptage
        résolus associés à ce produit.

        Contrairement à l'ancienne logique qui additionnait les quantités de comptage (5+3+2=10),
        cette logique utilise les résultats finaux validés après résolution des écarts.

        Exclut les articles avec le code produit '1111111111111' de la consolidation.

        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID du magasin

        Returns:
            Liste de dictionnaires avec les données consolidées
        """

        # Logique simplifiée : Σ(final_result) par produit depuis EcartComptage résolus
        # Plus de jointures complexes avec counting_sequences

        # Étape 1 : Récupérer les IDs des produits à exclure (code test)
        excluded_product_ids = Product.objects.filter(
            Internal_Product_Code='111111111111111'
        ).values_list('id', flat=True)

        # Étape 2 : Récupérer les produits avec leur somme de final_result
        # Solution : d'abord identifier les produits des EcartComptage, puis sommer
        # Pour éviter les duplications si un EcartComptage a plusieurs CountingSequence

        # Étape 2a : Récupérer les paires (ecart_id, product_id) uniques
        ecart_product_pairs = EcartComptage.objects.filter(
            inventory_id=inventory_id,
            resolved=True,
            final_result__isnull=False,
            counting_sequences__counting_detail__job__warehouse_id=warehouse_id,
        ).values(
            'id',  # EcartComptage ID pour unicité
            'counting_sequences__counting_detail__product_id'
        ).distinct()

        # Étape 2b : Créer un mapping ecart_id -> product_id (premier produit trouvé)
        ecart_to_product = {}
        for pair in ecart_product_pairs:
            ecart_id = pair['id']
            product_id = pair['counting_sequences__counting_detail__product_id']
            if ecart_id not in ecart_to_product:
                ecart_to_product[ecart_id] = product_id

        # Étape 2c : Récupérer les EcartComptage avec leur produit et sommer par produit
        consolidated_data = []
        product_sums = {}

        ecart_comptages = EcartComptage.objects.filter(
            id__in=ecart_to_product.keys()
        ).select_related()

        for ecart in ecart_comptages:
            product_id = ecart_to_product[ecart.id]
            if product_id not in product_sums:
                product_sums[product_id] = 0
            product_sums[product_id] += ecart.final_result

        # Convertir en format attendu
        for product_id, total_quantity in product_sums.items():
            consolidated_data.append({
                'product_id': product_id,
                'total_quantity': total_quantity
            })

        # Appliquer l'exclusion des produits test
        consolidated_data = [
            item for item in consolidated_data
            if item['product_id'] not in excluded_product_ids
        ]

        # Récupérer les détails des produits
        product_ids = [item['product_id'] for item in consolidated_data]
        products = Product.objects.filter(id__in=product_ids).select_related('Product_Family')

        # Créer un mapping produit_id -> détails produit
        products_map = {}
        for product in products:
            products_map[product.id] = {
                'product_reference': product.reference,
                'product_code': product.Internal_Product_Code,
                'product_description': product.Short_Description or '',
                'product_barcode': product.Barcode or '',
                'product_unit': product.Stock_Unit or '',
                'product_family': product.Product_Family.family_name if product.Product_Family else '',
            }

        # Combiner les données
        result = []
        for item in consolidated_data:
            product_id = item['product_id']
            if product_id in products_map:
                product_data = products_map[product_id].copy()
                product_data.update({
                    'product_id': product_id,
                    'total_quantity': item['total_quantity'] or 0,
                })
                result.append(product_data)

        return result
    

