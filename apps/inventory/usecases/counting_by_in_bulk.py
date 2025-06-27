"""
Use case pour le comptage en lot (bulk counting).
"""
from typing import Dict, Any
from ..models import Counting, Inventory
from ..exceptions import CountingValidationError

# --- Définition des règles de validation ---
def rule_order_required(data):
    if not data.get('order'):
        return "- L'ordre du comptage est obligatoire."
    return None

def rule_unit_scanned_entry_quantity(data):
    if data.get('unit_scanned') and data.get('entry_quantity'):
        return "- Pour le mode 'en vrac', unit_scanned et entry_quantity ne peuvent pas être true simultanément."
    return None

def rule_unit_scanned_block(data):
    if not data.get('unit_scanned') and not data.get('entry_quantity'):
        return "- Pour le mode 'en vrac', au moins un des champs unit_scanned ou entry_quantity doit être true."
    return None

def rule_entry_quantity_block(data):
    if data.get('stock_situation'):
        return "- Pour le mode 'en vrac', stock_situation doit être false."
    return None

BULK_RULES = [
    rule_order_required,
    rule_unit_scanned_entry_quantity,
    rule_unit_scanned_block,
    rule_entry_quantity_block,
]

class CountingByInBulk:
    """
    Use case pour gérer le comptage d'inventaire en vrac (en lot).
    Validation déclarative par liste de règles.
    """
    
    def validate_counting_data(self, data: Dict[str, Any]) -> None:
        """
        Valide les données du comptage sans créer l'objet.
        
        Args:
            data: Données du comptage à valider
            
        Raises:
            CountingValidationError: Si les données sont invalides
        """
        errors = [rule(data) for rule in BULK_RULES if rule(data)]
        if errors:
            raise CountingValidationError("\n" + "\n".join(errors))
    
    def create_counting(self, data: Dict[str, Any]) -> Counting:
        # Validation des données
        self.validate_counting_data(data)
        
        try:
            inventory = Inventory.objects.get(id=data['inventory_id'])
        except Inventory.DoesNotExist:
            raise CountingValidationError(f"Inventaire avec l'ID {data['inventory_id']} non trouvé")
        counting = Counting.objects.create(
            inventory=inventory,
            order=data['order'],
            count_mode=data['count_mode'],
            unit_scanned=data.get('unit_scanned', False),
            entry_quantity=data.get('entry_quantity', False),
            is_variant=data.get('is_variant', False),
            stock_situation=data.get('stock_situation', False),
            quantity_show=data.get('quantity_show', False),
            show_product=data.get('show_product', False),
        )
        return counting 