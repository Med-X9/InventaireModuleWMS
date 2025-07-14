"""
Use case pour le comptage basé sur l'image de stock.
"""
from typing import Dict, Any
from ..models import Counting,  Inventory
from ..exceptions import CountingValidationError


class CountingByStockimage:
    """
    Use case pour gérer le comptage d'inventaire basé sur l'image de stock.
    
    Ce use case permet de :
    - Créer des comptages en mode "image de stock" avec la configuration appropriée
    """
    
    def __init__(self):
        self.counting_service = None  # Sera injecté via DI

    def validate_counting_data(self, data: Dict[str, Any]) -> None:
        """
        Valide les données du comptage sans créer l'objet.
        
        Args:
            data: Données du comptage à valider
            
        Raises:
            CountingValidationError: Si les données sont invalides
        """
        # Règles de validation pour le mode "image de stock"
        validation_rules = [
            (lambda d: not d.get('order'), "L'ordre du comptage est obligatoire"),
            (lambda d: not d.get('stock_situation'), "Pour le mode 'image de stock', le champ stock_situation doit être true"),
            (lambda d: d.get('unit_scanned'), "Pour le mode 'image de stock', le champ unit_scanned doit être false"),
            (lambda d: d.get('entry_quantity'), "Pour le mode 'image de stock', le champ entry_quantity doit être false"),
            (lambda d: d.get('is_variant'), "Pour le mode 'image de stock', le champ is_variant doit être false"),
            (lambda d: d.get('n_lot'), "Pour le mode 'image de stock', le champ n_lot doit être false"),
            (lambda d: d.get('n_serie'), "Pour le mode 'image de stock', le champ n_serie doit être false"),
            (lambda d: d.get('dlc'), "Pour le mode 'image de stock', le champ dlc doit être false"),
            (lambda d: d.get('show_product'), "Pour le mode 'image de stock', le champ show_product doit être false"),
            (lambda d: d.get('quantity_show'), "Pour le mode 'image de stock', le champ quantity_show doit être false"),
        ]
        
        # Application des règles de validation
        errors = [error_msg for rule, error_msg in validation_rules if rule(data)]
        
        if errors:
            raise CountingValidationError(" | ".join(errors))

    def create_counting(self, data: Dict[str, Any]) -> Counting:
        # Validation des données
        self.validate_counting_data(data)
        
        # Récupération de l'inventaire
        try:
            inventory = Inventory.objects.get(id=data['inventory_id'])
        except Inventory.DoesNotExist:
            raise CountingValidationError(f"Inventaire avec l'ID {data['inventory_id']} non trouvé")
        
        # Configuration par défaut pour le mode "image de stock"
        counting_config = {
            'inventory': inventory,
            'order': data['order'],
            'count_mode': data['count_mode'],
            'unit_scanned': False,
            'entry_quantity': False,
            'is_variant': False,
            'n_lot': False,
            'n_serie': False,
            'dlc': False,
            'show_product': False,
            'stock_situation': True,
            'quantity_show': False,
        }
        
        # Créer l'objet Counting sans sauvegarder
        counting = Counting(**counting_config)
        
        # Générer la référence manuellement
        counting.reference = counting.generate_reference(counting.REFERENCE_PREFIX)
        
        # Sauvegarder l'objet
        counting.save()
        
        return counting 