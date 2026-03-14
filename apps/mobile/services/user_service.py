from django.utils import timezone
from apps.mobile.repositories.user_repository import UserRepository
from apps.mobile.exceptions.user_exceptions import (
    ProductNotFoundException,
    LocationNotFoundException,
    StockNotFoundException
)
from apps.mobile.exceptions.auth_exceptions import (
    UserNotFoundException
)
from apps.mobile.exceptions.inventory_exceptions import (
    AccountNotFoundException,
    DatabaseConnectionException,
    DataValidationException
)


class UserService:
    """Service pour la gestion des données utilisateur"""
    
    def __init__(self):
        self.repository = UserRepository()
    
    def get_user_inventories(self, user_id):
        """Récupère les inventaires du même compte qu'un utilisateur"""
        try:
            # Récupérer les inventaires via le repository
            inventories = self.repository.get_inventories_by_user_account(user_id)
            
            # Préparer la réponse
            response_data = {
                'success': True,
                'user_id': user_id,
                'timestamp': timezone.now().isoformat(),
                'data': {
                    'inventories': []
                }
            }
            
            # Formater les données des inventaires
            for inventory in inventories:
                try:
                    warehouse_info = self.repository.get_warehouse_info_for_inventory(inventory)
                    inv_data = self.repository.format_inventory_data(inventory, warehouse_info)
                    response_data['data']['inventories'].append(inv_data)
                except Exception as e:
                    print(f"Erreur lors du traitement de l'inventaire {inventory.id}: {str(e)}")
                    continue
            
            # Logger la récupération
            
            return response_data
            
        except Exception as e:
            print(f"Erreur lors de la récupération des inventaires: {str(e)}")
            raise e
    
    def get_user_products(self, user_id):
        """Récupère les produits du même compte qu'un utilisateur"""
        try:
            # Validation des paramètres
            if not user_id:
                raise DataValidationException("ID utilisateur requis")
            
            # Récupérer les produits via le repository
            products = self.repository.get_products_by_user_account(user_id)
            
            # Préparer la réponse
            response_data = {
                'success': True,
                'user_id': user_id,
                'timestamp': timezone.now().isoformat(),
                'data': {
                    'products': []
                }
            }
            
            # Formater les données des produits
            formatted_products = []
            for product in products:
                try:
                    product_data = self.repository.format_product_data(product)
                    formatted_products.append(product_data)
                except Exception as e:
                    print(f"Erreur lors du formatage du produit {product.id}: {str(e)}")
                    # Continuer avec les autres produits même si un échoue
                    continue
            
            response_data['data']['products'] = formatted_products
            
            # Logger la récupération
            
            return response_data
            
        except (ProductNotFoundException, DataValidationException, DatabaseConnectionException) as e:
            # Re-raise les exceptions spécifiques
            raise
        except Exception as e:
            print(f"Erreur inattendue lors de la récupération des produits: {str(e)}")
            import traceback
            print(f"Traceback complet: {traceback.format_exc()}")
            raise DatabaseConnectionException(f"Erreur inattendue lors de la récupération des produits: {str(e)}")
    
    def get_user_locations(self, user_id):
        """Récupère les locations du même compte qu'un utilisateur"""
        try:
            # Validation des paramètres
            if not user_id:
                raise DataValidationException("ID utilisateur requis")
            
            # Récupérer les locations via le repository
            locations = self.repository.get_locations_by_user_account(user_id)
            
            # Préparer la réponse
            response_data = {
                'success': True,
                'user_id': user_id,
                'timestamp': timezone.now().isoformat(),
                'data': {
                    'locations': []
                }
            }
            
            # Formater les données des locations
            formatted_locations = []
            for location in locations:
                try:
                    location_data = self.repository.format_location_data(location)
                    formatted_locations.append(location_data)
                except Exception as e:
                    print(f"Erreur lors du formatage de la location {location.id}: {str(e)}")
                    # Continuer avec les autres locations même si une échoue
                    continue
            
            response_data['data']['locations'] = formatted_locations
            
            # Logger la récupération            
            return response_data
            
        except (LocationNotFoundException, DataValidationException, DatabaseConnectionException) as e:
            # Re-raise les exceptions spécifiques
            raise
        except Exception as e:
            print(f"Erreur inattendue lors de la récupération des locations: {str(e)}")
            import traceback
            print(f"Traceback complet: {traceback.format_exc()}")
            raise DatabaseConnectionException(f"Erreur inattendue lors de la récupération des locations: {str(e)}")
    
    def get_user_stocks(self, user_id):
        """Récupère les stocks du même compte qu'un utilisateur"""
        try:
            # Validation des paramètres
            if not user_id:
                raise DataValidationException("ID utilisateur requis")
            
            # Récupérer les stocks via le repository
            stocks = self.repository.get_stocks_by_user_account(user_id)
            
            # Préparer la réponse
            response_data = {
                'success': True,
                'user_id': user_id,
                'timestamp': timezone.now().isoformat(),
                'data': {
                    'stocks': []
                }
            }
            
            # Formater les données des stocks
            formatted_stocks = []
            for stock in stocks:
                try:
                    stock_data = self.repository.format_stock_data(stock)
                    formatted_stocks.append(stock_data)
                except Exception as e:
                    print(f"Erreur lors du formatage du stock {stock.id}: {str(e)}")
                    # Continuer avec les autres stocks même si un échoue
                    continue
            
            response_data['data']['stocks'] = formatted_stocks
                        
            return response_data
            
        except (StockNotFoundException, DataValidationException, DatabaseConnectionException) as e:
            # Re-raise les exceptions spécifiques
            raise
        except Exception as e:
            print(f"Erreur inattendue lors de la récupération des stocks: {str(e)}")
            import traceback
            print(f"Traceback complet: {traceback.format_exc()}")
            raise DatabaseConnectionException(f"Erreur inattendue lors de la récupération des stocks: {str(e)}") 