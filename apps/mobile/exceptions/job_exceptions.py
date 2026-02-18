"""
Exceptions pour la gestion des jobs dans l'application mobile.
"""


class JobException(Exception):
    """Exception de base pour les jobs (contexte mobile)."""
    pass


class JobFilterValidationException(JobException):
    """Exception levée lorsque les paramètres de filtrage des jobs sont invalides."""
    pass


class WarehouseNotFoundException(JobException):
    """Exception levée lorsque l'entrepôt demandé n'existe pas."""
    pass
