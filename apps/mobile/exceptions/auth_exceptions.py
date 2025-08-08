class AuthException(Exception):
    """Exception de base pour l'authentification"""
    pass


class UserNotFoundException(AuthException):
    """Exception levée quand un utilisateur n'est pas trouvé"""
    pass


class InvalidCredentialsException(AuthException):
    """Exception levée quand les identifiants sont invalides"""
    pass


class TokenInvalidException(AuthException):
    """Exception levée quand un token est invalide"""
    pass


class UserInactiveException(AuthException):
    """Exception levée quand un utilisateur est inactif"""
    pass 