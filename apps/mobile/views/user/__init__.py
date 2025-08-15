# Import des vues utilisateur
from .user_products_view import UserProductsView
from .user_locations_view import UserLocationsView
from .user_stocks_view import UserStocksView

__all__ = [
    'UserProductsView',
    'UserLocationsView',
    'UserStocksView'
]
