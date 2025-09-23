"""
Exceptions pour la gestion des CountingDetail dans l'app mobile.
"""

class CountingDetailValidationError(Exception):
    """Exception levée lors d'une erreur de validation des données CountingDetail."""
    pass

class ProductPropertyValidationError(Exception):
    """Exception levée lors d'une erreur de validation des propriétés du produit."""
    pass

class CountingAssignmentValidationError(Exception):
    """Exception levée lors d'une erreur de validation de l'assignment."""
    pass

class JobDetailValidationError(Exception):
    """Exception levée lors d'une erreur de validation du JobDetail."""
    pass

class NumeroSerieValidationError(Exception):
    """Exception levée lors d'une erreur de validation des numéros de série."""
    pass

class CountingModeValidationError(Exception):
    """Exception levée lors d'une erreur de validation du mode de comptage."""
    pass

class CountingDetailBatchError(Exception):
    """Exception levée lors d'une erreur dans le traitement en lot des CountingDetail."""
    pass

class CountingDetailNotFoundError(Exception):
    """Exception levée lorsqu'un CountingDetail n'est pas trouvé."""
    pass

class CountingDetailUpdateError(Exception):
    """Exception levée lors d'une erreur de mise à jour d'un CountingDetail."""
    pass
