"""
Repository pour les opérations de données pour l'export Excel consolidé
"""
from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q
from ..models import Inventory, CountingDetail, Counting, EcartComptage, ComptageSequence
from apps.masterdata.models import Location


class ExcelExportRepository:
    """Repository pour l'export Excel consolidé par article"""
    
    def get_inventory_by_id(self, inventory_id: int) -> Optional[Inventory]:
        """Récupère un inventaire par ID"""
        try:
            return Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            return None
    
    def check_countings_for_export(
        self, 
        inventory_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si les comptages d'ordre 2 et 3 existent et ont le mode "par article".
        Cette vérification sert uniquement à valider le mode de comptage, pas à filtrer les données.
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            Tuple (is_valid, error_message):
            - is_valid: True si les conditions sont remplies, False sinon
            - error_message: Message d'erreur si is_valid est False, None sinon
        """
        # Récupérer l'inventaire pour le nom dans le message d'erreur
        inventory = self.get_inventory_by_id(inventory_id)
        inventory_label = inventory.label if inventory else f"ID {inventory_id}"
        
        # Vérifier que les comptages d'ordre 2 et 3 existent
        counting_order_2 = Counting.objects.filter(
            inventory_id=inventory_id,
            order=2
        ).first()
        
        counting_order_3 = Counting.objects.filter(
            inventory_id=inventory_id,
            order=3
        ).first()
        
        if not counting_order_2:
            return False, "Le comptage d'ordre 2 n'existe pas pour cet inventaire."
        
        if not counting_order_3:
            return False, "Le comptage d'ordre 3 n'existe pas pour cet inventaire."
        
        # Vérifier que les deux comptages ont le mode "par article"
        if counting_order_2.count_mode.lower() != 'par article':
            return False, "Le mode de comptage de cet inventaire n'est pas 'par article'."
        
        if counting_order_3.count_mode.lower() != 'par article':
            return False, "Le mode de comptage de cet inventaire n'est pas 'par article'."
        
        return True, None
    
    def get_consolidated_data_by_inventory(
        self,
        inventory_id: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère les données consolidées par article pour un inventaire.

        Utilise UNIQUEMENT le final_result des EcartComptage RÉSOLUS.

        Pour chaque produit apparaissant dans des EcartComptage résolus,
        la quantité consolidée est la SOMME des final_result de TOUS les EcartComptage
        résolus associés à ce produit.

        Contrairement à l'ancienne logique qui additionnait les quantités de comptage (5+3+2=10),
        cette logique utilise les résultats finaux validés après résolution des écarts.

        Exclut les articles avec le code produit '1111111111111' de la consolidation.

        Args:
            inventory_id: ID de l'inventaire

        Returns:
            Liste de dictionnaires avec les données consolidées
        """

        # Logique simplifiée : Σ(final_result) par produit depuis EcartComptage résolus
        # Plus de jointures complexes avec counting_sequences

        from django.db.models import Sum, F
        from ..models import Product

        # Récupérer les produits avec leur somme de final_result
        # Jointure directe : EcartComptage -> CountingSequence -> CountingDetail -> Product
        consolidated_data = EcartComptage.objects.filter(
            inventory_id=inventory_id,
            resolved=True,
            final_result__isnull=False
        ).values(
            'counting_sequences__counting_detail__product_id'
        ).annotate(
            total_quantity=Sum('final_result'),
            product_id=F('counting_sequences__counting_detail__product_id')
        ).exclude(
            counting_sequences__counting_detail__product__Internal_Product_Code='111111111111111'
        ).distinct()

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
    

