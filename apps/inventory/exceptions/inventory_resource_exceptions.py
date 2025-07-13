"""
Exceptions pour l'affectation des ressources aux inventaires.
"""

class InventoryResourceValidationError(Exception):
    """Exception levée lors d'une erreur de validation des données d'affectation"""
    pass

class InventoryResourceBusinessRuleError(Exception):
    """Exception levée lors d'une violation de règle métier"""
    pass

class InventoryResourceNotFoundError(Exception):
    """Exception levée quand une ressource ou un inventaire n'est pas trouvé"""
    pass

class InventoryResourceConflictError(Exception):
    """Exception levée lors d'un conflit d'affectation"""
    pass 