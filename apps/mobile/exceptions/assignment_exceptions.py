class AssignmentNotFoundException(Exception):
    """Exception levée quand un assignment n'est pas trouvé"""
    pass


class UserNotAssignedException(Exception):
    """Exception levée quand un utilisateur n'est pas affecté à un assignment"""
    pass


class InvalidStatusTransitionException(Exception):
    """Exception levée quand une transition de statut n'est pas autorisée"""
    pass


class JobNotFoundException(Exception):
    """Exception levée quand un job n'est pas trouvé"""
    pass


class AssignmentValidationException(Exception):
    """Exception levée lors de la validation d'un assignment"""
    pass


class AssignmentAlreadyStartedException(Exception):
    """Exception levée quand on tente de modifier un assignment déjà entamé"""
    pass