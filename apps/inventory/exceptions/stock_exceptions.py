class StockValidationError(Exception):
    """Exception levée lors d'une erreur de validation de stock."""
    pass

class StockNotFoundError(Exception):
    """Exception levée quand un stock n'est pas trouvé."""
    pass

class StockImportError(Exception):
    """Exception levée lors d'une erreur d'import de stock."""
    pass 