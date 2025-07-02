class AssignmentError(Exception):
    """Exception de base pour les erreurs d'affectation"""
    pass

class AssignmentNotFoundError(AssignmentError):
    """Exception levée quand une affectation n'est pas trouvée"""
    pass

class AssignmentValidationError(AssignmentError):
    """Exception levée quand les données d'affectation sont invalides"""
    pass

class AssignmentBusinessRuleError(AssignmentError):
    """Exception levée quand une règle métier d'affectation n'est pas respectée"""
    pass

class AssignmentSessionError(AssignmentError):
    """Exception levée quand il y a un problème avec l'affectation de session"""
    pass 