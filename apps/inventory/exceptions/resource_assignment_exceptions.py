class ResourceAssignmentValidationError(Exception):
    """Exception levée lors d'une erreur de validation des données d'affectation des ressources"""
    pass

class ResourceAssignmentBusinessRuleError(Exception):
    """Exception levée lors d'une violation de règle métier pour l'affectation des ressources"""
    pass

class ResourceAssignmentNotFoundError(Exception):
    """Exception levée quand une ressource ou un job n'est pas trouvé"""
    pass

class ResourceAssignmentConflictError(Exception):
    """Exception levée lors d'un conflit d'affectation de ressources"""
    pass 