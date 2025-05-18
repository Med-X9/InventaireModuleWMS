class PlanningCreationError(Exception):
    """Exception levée lors d'une erreur de création de planning"""
    pass

class PlanningNotFoundError(Exception):
    """Exception levée quand un planning n'est pas trouvé"""
    pass

class PlanningDateError(Exception):
    """Exception levée lors d'une erreur de date dans le planning"""
    pass 