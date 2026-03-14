"""
Exceptions spécifiques pour les CountingDetail et NumeroSerie.
"""

class CountingDetailValidationError(Exception):
    """Exception levée lors de la validation des données de CountingDetail."""
    pass


class ProductPropertyValidationError(Exception):
    """Exception levée lors de la validation des propriétés d'un produit."""
    pass


class CountingAssignmentValidationError(Exception):
    """Exception levée lors de la validation d'un assignment dans le contexte du comptage."""
    pass


class JobDetailValidationError(Exception):
    """Exception levée lors de la validation d'un JobDetail."""
    pass


class NumeroSerieValidationError(Exception):
    """Exception levée lors de la validation des numéros de série."""
    pass


class CountingModeValidationError(Exception):
    """Exception levée lors de la validation du mode de comptage."""
    pass
