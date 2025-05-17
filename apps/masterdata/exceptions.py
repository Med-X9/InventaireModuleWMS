class WarehouseNotFoundError(Exception):
    """Exception levée lorsqu'un entrepôt n'est pas trouvé"""
    pass

class ZoneNotFoundError(Exception):
    """Exception levée lorsqu'une zone n'est pas trouvée"""
    pass

class LocationNotFoundError(Exception):
    """Exception levée lorsqu'une location n'est pas trouvée"""
    pass

class AccountNotFoundError(Exception):
    """Exception levée lorsqu'un compte n'est pas trouvé"""
    pass 