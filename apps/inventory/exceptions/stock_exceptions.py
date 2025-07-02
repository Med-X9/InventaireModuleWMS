"""
Exceptions spécifiques à la gestion des stocks.
"""


class StockValidationError(Exception):
    """
    Exception levée lors d'une erreur de validation des données de stock.
    """
    pass


class StockNotFoundError(Exception):
    """
    Exception levée quand un stock n'est pas trouvé.
    """
    pass


class StockImportError(Exception):
    """
    Exception levée lors d'une erreur d'import de stocks.
    """
    pass


class StockDuplicateError(Exception):
    """
    Exception levée quand un stock en double est détecté.
    """
    pass 