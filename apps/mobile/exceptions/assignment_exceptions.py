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


class PersonValidationException(Exception):
    """Exception levée lors de la validation des personnes pour un assignment"""
    pass


class AssignmentNotEntameException(Exception):
    """Exception levée quand on tente de bloquer un assignment qui n'est pas en statut ENTAME"""
    pass


class AssignmentNotBloqueException(Exception):
    """Exception levée quand on tente de débloquer un assignment qui n'est pas en statut bloqué"""
    pass


class MaxEntameAssignmentsException(Exception):
    """Exception levée quand l'utilisateur a déjà atteint le maximum d'assignments ENTAME (3) pour le même inventory"""
    pass