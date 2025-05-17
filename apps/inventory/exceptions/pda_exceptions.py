class PdaCreationError(Exception):
    """Exception levée lors d'une erreur de création de PDA"""
    pass

class PdaNotFoundError(Exception):
    """Exception levée quand un PDA n'est pas trouvé"""
    pass

class PdaLabelError(Exception):
    """Exception levée lors d'une erreur de label de PDA"""
    pass 