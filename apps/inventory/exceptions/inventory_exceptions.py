"""
Exceptions personnalisées pour l'application inventory.
"""

class InventoryError(Exception):
    """Classe de base pour toutes les exceptions de l'application inventory."""
    pass

class InventoryValidationError(InventoryError):
    """Exception levée lors de la validation des données d'inventaire."""
    pass

class InventoryNotFoundError(InventoryError):
    """Exception levée lorsqu'un inventaire n'est pas trouvé."""
    pass

class CountingError(InventoryError):
    """Classe de base pour les erreurs liées aux comptages."""
    pass

class CountingValidationError(CountingError):
    """Exception levée lors d'une erreur de validation d'un comptage."""
    pass

class InventoryCreationError(Exception):
    """Exception levée lors d'une erreur de création d'inventaire"""
    pass

class InventoryStatusError(Exception):
    """Exception levée lors d'une erreur de statut d'inventaire"""
    pass

class InventoryDateError(Exception):
    """Exception levée lors d'une erreur de date dans l'inventaire"""
    pass 