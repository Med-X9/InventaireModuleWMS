class UserException(Exception):
    """Exception de base pour les données utilisateur"""
    pass


class ProductNotFoundException(UserException):
    """Exception levée quand aucun produit n'est trouvé"""
    pass


class LocationNotFoundException(UserException):
    """Exception levée quand aucune location n'est trouvée"""
    pass


class StockNotFoundException(UserException):
    """Exception levée quand aucun stock n'est trouvé"""
    pass 