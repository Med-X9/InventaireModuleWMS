class SyncException(Exception):
    """Exception de base pour la synchronisation"""
    pass


class SyncDataException(SyncException):
    """Exception levée lors de la synchronisation des données"""
    pass


class UploadDataException(SyncException):
    """Exception levée lors de l'upload de données"""
    pass


class JobNotFoundException(SyncException):
    """Exception levée quand un job n'est pas trouvé"""
    pass


class AssignmentNotFoundException(SyncException):
    """Exception levée quand une assignation n'est pas trouvée"""
    pass


class CountingNotFoundException(SyncException):
    """Exception levée quand un comptage n'est pas trouvé"""
    pass 