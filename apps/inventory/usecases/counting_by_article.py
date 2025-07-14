"""
Use case pour le comptage par article.
"""
from typing import Dict, Any
from ..models import Counting, Inventory
from ..exceptions import CountingValidationError

# --- Définition des règles de validation ---
def rule_order_required(data):
    if not data.get('order'):
        return "- L'ordre du comptage est obligatoire."
    return None

def rule_unit_scanned_false(data):
    if data.get('unit_scanned'):
        return "- Pour le mode 'par article', unit_scanned doit être false."
    return None

def rule_entry_quantity_false(data):
    if data.get('entry_quantity'):
        return "- Pour le mode 'par article', entry_quantity doit être false."
    return None

def rule_stock_situation_false(data):
    if data.get('stock_situation'):
        return "- Pour le mode 'par article', stock_situation doit être false."
    return None

def rule_n_serie_exclusif(data):
    if data.get('n_serie') and data.get('n_lot'):
        return "- Pour le mode 'par article', n_serie et n_lot ne peuvent pas être true simultanément."
    return None

ARTICLE_RULES = [
    rule_order_required,
    rule_unit_scanned_false,
    rule_entry_quantity_false,
    rule_stock_situation_false,
    rule_n_serie_exclusif,
]

class CountingByArticle:
    """
    Use case pour gérer le comptage d'inventaire par article.
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
        errors = [rule(data) for rule in ARTICLE_RULES if rule(data)]
        if errors:
            raise CountingValidationError("\n" + "\n".join(errors))
    
    def create_counting(self, data: Dict[str, Any]) -> Counting:
        # Validation des données
        self.validate_counting_data(data)
        
        try:
            inventory = Inventory.objects.get(id=data['inventory_id'])
        except Inventory.DoesNotExist:
            raise CountingValidationError(f"Inventaire avec l'ID {data['inventory_id']} non trouvé")
        
        # Créer l'objet Counting sans sauvegarder
        counting = Counting(
            inventory=inventory,
            order=data['order'],
            count_mode=data['count_mode'],
            unit_scanned=data.get('unit_scanned', False),
            entry_quantity=data.get('entry_quantity', False),
            is_variant=data.get('is_variant', False),
            stock_situation=data.get('stock_situation', False),
            quantity_show=data.get('quantity_show', False),
            n_lot=data.get('n_lot', False),
            n_serie=data.get('n_serie', False),
            dlc=data.get('dlc', False),
        )
        
        # Générer la référence manuellement
        counting.reference = counting.generate_reference(counting.REFERENCE_PREFIX)
        
        # Sauvegarder l'objet
        counting.save()
        
        return counting 