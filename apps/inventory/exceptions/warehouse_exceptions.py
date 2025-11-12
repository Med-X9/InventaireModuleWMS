class WarehouseAccountValidationError(Exception):
    """Exception levée lorsque les données fournies pour la récupération des entrepôts sont invalides."""


class WarehouseAccountNotFoundError(Exception):
    """Exception levée lorsque aucun entrepôt n'est trouvé pour un compte donné."""

