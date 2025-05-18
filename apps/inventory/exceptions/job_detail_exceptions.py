class JobDetailCreationError(Exception):
    """Exception levée lors d'une erreur de création de job detail"""
    pass

class JobDetailNotFoundError(Exception):
    """Exception levée quand un job detail n'est pas trouvé"""
    pass

class JobDetailStatusError(Exception):
    """Exception levée lors d'une erreur de statut de job detail"""
    pass 