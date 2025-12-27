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
        Utilise le final_result des EcartComptage qui ont un résultat final défini
        (soit résolus, soit ayant un final_result explicite).

        Exclut les articles avec le code produit '1111111111111' de la consolidation.

        Retourne une liste de dictionnaires avec :
        - Les informations de l'article
        - La quantité consolidée (somme de tous les final_result des EcartComptage résolus)
        - Les emplacements où l'article est présent

        Args:
            inventory_id: ID de l'inventaire

        Returns:
            Liste de dictionnaires avec les données consolidées
        """
        # Récupérer les EcartComptage avec résultat final défini de l'inventaire
        # Inclure les écarts résolus OU ayant un final_result défini
        ecart_comptages = EcartComptage.objects.filter(
            inventory_id=inventory_id
        ).filter(
            Q(resolved=True) | Q(final_result__isnull=False)  # Écarts résolus OU avec résultat final
        ).select_related(
            'inventory'  # Relation directe ForeignKey uniquement
        ).prefetch_related(
            'counting_sequences__counting_detail__product',
            'counting_sequences__counting_detail__product__Product_Family',
            'counting_sequences__counting_detail__location'
        ).exclude(
            counting_sequences__counting_detail__product__Internal_Product_Code='1111111111111'
        )

        # Convertir en liste pour pouvoir itérer plusieurs fois si nécessaire
        ecart_comptages_list = list(ecart_comptages)

        # Grouper par produit et consolider
        products_data = {}

        for ecart in ecart_comptages_list:
            # Récupérer les détails de comptage associés à cet écart
            for sequence in ecart.counting_sequences.all():
                counting_detail = sequence.counting_detail
                product = counting_detail.product
                location = counting_detail.location

                if not product:
                    continue

                product_id = product.id
                location_ref = location.location_reference if location else ''

                if product_id not in products_data:
                    # Initialiser les données du produit
                    products_data[product_id] = {
                        'product_id': product_id,
                        'product_reference': product.reference,
                        'product_code': product.Internal_Product_Code,
                        'product_description': product.Short_Description or '',
                        'product_barcode': product.Barcode or '',
                        'product_unit': product.Stock_Unit or '',
                        'product_family': product.Product_Family.family_name if product.Product_Family else '',
                        'total_quantity': 0,
                        'locations_set': set()  # Set pour stocker les références d'emplacements uniques
                    }

                # Utiliser le final_result de l'EcartComptage
                products_data[product_id]['total_quantity'] += ecart.final_result

                # Ajouter l'emplacement à la liste des emplacements (set pour éviter les doublons)
                if location_ref:
                    products_data[product_id]['locations_set'].add(location_ref)

        # Convertir en liste et transformer le set d'emplacements en liste triée
        result = []
        for product_data in products_data.values():
            # Convertir le set en liste triée
            product_data['locations_list'] = sorted(list(product_data['locations_set']))
            # Retirer le set de la structure de données
            del product_data['locations_set']
            result.append(product_data)

        return result
    

