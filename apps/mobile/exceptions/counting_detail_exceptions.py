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

class EcartComptageResoluError(Exception):
    """
    Exception levée quand on essaie d'ajouter un comptage à un écart résolu.
    """
    def __init__(self, ecart, product, location):
        self.ecart = ecart
        self.product = product
        self.location = location
        product_name = getattr(product, 'Short_Description', str(product))
        location_code = getattr(location, 'code', str(location))
        
        message = (
            f"Les comptages pour cet emplacement sont terminés. "
            f"Écart {ecart.reference} déjà résolu. "
            f"Impossible d'ajouter un nouveau comptage pour "
            f"Produit: {product_name}, "
            f"Location: {location_code}"
        )
        super().__init__(message)