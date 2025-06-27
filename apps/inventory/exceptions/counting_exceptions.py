class CountingError(Exception):
    """Exception de base pour les erreurs de comptage"""
    pass


class CountingNotFoundError(CountingError):
    """Exception levée quand un comptage n'est pas trouvé"""
    pass


class CountingValidationError(CountingError):
    """Exception levée quand les données de comptage sont invalides"""
    pass


class CountingCreationError(CountingError):
    """Exception levée lors de la création d'un comptage"""
    pass


class CountingUpdateError(CountingError):
    """Exception levée lors de la mise à jour d'un comptage"""
    pass


class CountingDeletionError(CountingError):
    """Exception levée lors de la suppression d'un comptage"""
    pass 