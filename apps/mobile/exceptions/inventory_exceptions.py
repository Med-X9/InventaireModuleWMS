class InventoryException(Exception):
    """Exception de base pour les inventaires"""
    pass


class InventoryNotFoundException(InventoryException):
    """Exception levée quand un inventaire n'est pas trouvé"""
    pass


class AccountNotFoundException(InventoryException):
    """Exception levée quand un compte n'est pas trouvé"""
    pass


class DatabaseConnectionException(InventoryException):
    """Exception levée lors de problèmes de connexion à la base de données"""
    pass


class DataValidationException(InventoryException):
    """Exception levée lors de problèmes de validation des données"""
    pass 