class JobCreationError(Exception):
    """Exception levée lors d'une erreur de création de job"""
    pass

class JobNotFoundError(Exception):
    """Exception levée quand un job n'est pas trouvé"""
    pass

class JobStatusError(Exception):
    """Exception levée lors d'une erreur de statut de job"""
    pass 