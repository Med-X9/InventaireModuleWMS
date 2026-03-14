from apps.inventory.models import Inventory, Job, Setting
from apps.masterdata.models import Warehouse, Product, Location, Stock
from apps.users.models import UserApp
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


class UserRepository:
    """Repository pour la gestion des données utilisateur"""
    
    def get_inventories_by_user_account(self, user_id):
        """Récupère les inventaires du même compte qu'un utilisateur"""
        try:
            # Récupérer l'utilisateur
            user = UserApp.objects.get(id=user_id)
            
            # Récupérer le compte de l'utilisateur
            account = user.compte
            if not account:
                raise AccountNotFoundException(f"Aucun compte associé à l'utilisateur {user_id}")
            
            # Récupérer tous les inventaires du même compte
            inventories = Inventory.objects.filter(
                awi_links__account=account,
                status='EN REALISATION'
            ).distinct().order_by('-created_at')
            
            return inventories
            
        except UserApp.DoesNotExist:
            raise UserNotFoundException(f"Utilisateur avec l'ID {user_id} non trouvé")
        except Exception as e:
            raise e
    
    def get_products_by_user_account(self, user_id):
        """Récupère les produits du même compte qu'un utilisateur"""
        try:
            # Validation de l'ID utilisateur
            if not user_id or not isinstance(user_id, int):
                raise DataValidationException(f"ID utilisateur invalide: {user_id}")
            
            # Récupérer l'utilisateur
            try:
                user = UserApp.objects.get(id=user_id)
            except UserApp.DoesNotExist:
                raise UserNotFoundException(f"Utilisateur avec l'ID {user_id} non trouvé")
            
            # Récupérer le compte de l'utilisateur
            account = user.compte
            
            if not account:
                raise AccountNotFoundException(f"Aucun compte associé à l'utilisateur {user_id}")
            
            # Vérifier si le compte est actif
            if account.account_statuts != 'ACTIVE':
                raise AccountNotFoundException(f"Le compte {account.account_name} n'est pas actif")
            
            # Récupérer tous les produits du même compte via la famille
            try:
                products = Product.objects.select_related('Product_Family').filter(
                    Product_Family__compte=account,
                    Product_Status='ACTIVE'
                ).order_by('Short_Description')
                
                # Si aucun produit trouvé, retourner une liste vide (pas d'exception)
                if products.count() == 0:
                    return []
                
                return products
                
            except Product.DoesNotExist:
                raise ProductNotFoundException(f"Aucun produit trouvé pour le compte {account.account_name}")
            except Exception as e:
                raise DatabaseConnectionException(f"Erreur de base de données lors de la récupération des produits: {str(e)}")
            
        except (UserNotFoundException, AccountNotFoundException, ProductNotFoundException, DataValidationException, DatabaseConnectionException):
            # Re-raise les exceptions spécifiques
            raise
        except Exception as e:
            raise DatabaseConnectionException(f"Erreur inattendue lors de la récupération des produits: {str(e)}")
    
    def get_locations_by_user_account(self, user_id):
        """Récupère les locations du même compte qu'un utilisateur"""
        try:
            # Validation de l'ID utilisateur
            if not user_id or not isinstance(user_id, int):
                raise DataValidationException(f"ID utilisateur invalide: {user_id}")
            
            # Récupérer l'utilisateur
            try:
                user = UserApp.objects.get(id=user_id)
            except UserApp.DoesNotExist:
                raise UserNotFoundException(f"Utilisateur avec l'ID {user_id} non trouvé")
            
            # Récupérer le compte de l'utilisateur
            account = user.compte
            
            if not account:
                raise AccountNotFoundException(f"Aucun compte associé à l'utilisateur {user_id}")
            
            # Vérifier si le compte est actif
            if account.account_statuts != 'ACTIVE':
                raise AccountNotFoundException(f"Le compte {account.account_name} n'est pas actif")
            
            # Récupérer toutes les locations du même compte via la chaîne: Location -> SousZone -> Zone -> Warehouse -> Setting -> Account
            try:
                # Récupérer d'abord les warehouses associés au compte via les settings
                warehouses = Warehouse.objects.filter(
                    awi_links__account=account
                ).distinct()
                
                # Puis récupérer les locations via ces warehouses
                locations = Location.objects.filter(
                    sous_zone__zone__warehouse__in=warehouses,
                    is_active=True
                ).order_by('location_reference')
                
                # Si aucune location trouvée, retourner une liste vide (pas d'exception)
                if locations.count() == 0:
                    return []
                
                return locations
                
            except Location.DoesNotExist:
                raise LocationNotFoundException(f"Aucune location trouvée pour le compte {account.account_name}")
            except Exception as e:
                raise DatabaseConnectionException(f"Erreur de base de données lors de la récupération des locations: {str(e)}")
            
        except (UserNotFoundException, AccountNotFoundException, LocationNotFoundException, DataValidationException, DatabaseConnectionException):
            # Re-raise les exceptions spécifiques
            raise
        except Exception as e:
            raise DatabaseConnectionException(f"Erreur inattendue lors de la récupération des locations: {str(e)}")
    
    def get_stocks_by_user_account(self, user_id):
        """Récupère les stocks du même compte qu'un utilisateur"""
        try:
            # Validation de l'ID utilisateur
            if not user_id or not isinstance(user_id, int):
                raise DataValidationException(f"ID utilisateur invalide: {user_id}")
            
            # Récupérer l'utilisateur
            try:
                user = UserApp.objects.get(id=user_id)
            except UserApp.DoesNotExist:
                raise UserNotFoundException(f"Utilisateur avec l'ID {user_id} non trouvé")
            
            # Récupérer le compte de l'utilisateur
            account = user.compte
            
            if not account:
                raise AccountNotFoundException(f"Aucun compte associé à l'utilisateur {user_id}")
            
            # Vérifier si le compte est actif
            if account.account_statuts != 'ACTIVE':
                raise AccountNotFoundException(f"Le compte {account.account_name} n'est pas actif")
            
            # Récupérer tous les stocks du même compte via la chaîne: Stock -> Location -> SousZone -> Zone -> Warehouse -> Setting -> Account
            try:
                # Récupérer d'abord les warehouses associés au compte via les settings
                warehouses = Warehouse.objects.filter(
                    awi_links__account=account
                ).distinct()
                
                # Puis récupérer les stocks via ces warehouses
                stocks = Stock.objects.filter(
                    location__sous_zone__zone__warehouse__in=warehouses
                ).order_by('reference')
                
                # Si aucun stock trouvé, retourner une liste vide (pas d'exception)
                if stocks.count() == 0:
                    return []
                
                return stocks
                
            except Stock.DoesNotExist:
                raise StockNotFoundException(f"Aucun stock trouvé pour le compte {account.account_name}")
            except Exception as e:
                raise DatabaseConnectionException(f"Erreur de base de données lors de la récupération des stocks: {str(e)}")
            
        except (UserNotFoundException, AccountNotFoundException, StockNotFoundException, DataValidationException, DatabaseConnectionException):
            # Re-raise les exceptions spécifiques
            raise
        except Exception as e:
            raise DatabaseConnectionException(f"Erreur inattendue lors de la récupération des stocks: {str(e)}")
    
    def get_warehouse_info_for_inventory(self, inventory):
        """Récupère les informations d'entrepôt pour un inventaire"""
        try:
            jobs = Job.objects.filter(inventory=inventory)
            if jobs.exists():
                first_job = jobs.first()
                return {
                    'warehouse_web_id': first_job.warehouse.id,
                    'warehouse_name': first_job.warehouse.warehouse_name
                }
            else:
                # Si pas de job, essayer via les settings
                settings = inventory.awi_links.all()
                if settings.exists():
                    first_setting = settings.first()
                    return {
                        'warehouse_web_id': first_setting.warehouse.id,
                        'warehouse_name': first_setting.warehouse.warehouse_name
                    }
                else:
                    return {
                        'warehouse_web_id': None,
                        'warehouse_name': None
                    }
        except Exception as e:
            return {
                'warehouse_web_id': None,
                'warehouse_name': None
            }
    
    def format_inventory_data(self, inventory, warehouse_info):
        """Formate les données d'un inventaire"""
        return {
            'web_id': inventory.id,
            'reference': inventory.reference,
            'label': inventory.label,
            'date': inventory.date.isoformat(),
            'status': inventory.status,
            'inventory_type': inventory.inventory_type,
            'warehouse_web_id': warehouse_info['warehouse_web_id'],
            'warehouse_name': warehouse_info['warehouse_name'],
            'en_preparation_status_date': inventory.en_preparation_status_date.isoformat() if inventory.en_preparation_status_date else None,
            'en_realisation_status_date': inventory.en_realisation_status_date.isoformat() if inventory.en_realisation_status_date else None,
            'termine_status_date': inventory.termine_status_date.isoformat() if inventory.termine_status_date else None,
            'cloture_status_date': inventory.cloture_status_date.isoformat() if inventory.cloture_status_date else None,
            'created_at': inventory.created_at.isoformat(),
            'updated_at': inventory.updated_at.isoformat()
        }
    
    def format_product_data(self, product):
        """Formate les données d'un produit"""
        try:
            # Vérifier si Product_Family existe
            family_name = None
            family_id = None
            if product.Product_Family:
                family_name = product.Product_Family.family_name
                family_id = product.Product_Family.id
            
            # Récupérer les numéros de série si le produit les supporte
            numeros_serie = []
            if product.n_serie:
                try:
                    from apps.masterdata.models import NSerie
                    nseries = NSerie.objects.filter(
                        product=product,
                        status='ACTIVE'
                    ).order_by('n_serie')
                    
                    for nserie in nseries:
                        numeros_serie.append({
                            'id': nserie.id,
                            'n_serie': nserie.n_serie,
                            'reference': nserie.reference,
                            'status': nserie.status,
                            'description': nserie.description,
                            'date_fabrication': nserie.date_fabrication.isoformat() if nserie.date_fabrication else None,
                            'date_expiration': nserie.date_expiration.isoformat() if nserie.date_expiration else None,
                            'warranty_end_date': nserie.warranty_end_date.isoformat() if nserie.warranty_end_date else None,
                            'is_expired': nserie.is_expired,
                            'is_warranty_valid': nserie.is_warranty_valid,
                            'created_at': nserie.created_at.isoformat(),
                            'updated_at': nserie.updated_at.isoformat()
                        })
                except Exception as e:
                    # Continuer sans les numéros de série en cas d'erreur
                    pass
            
            return {
                'web_id': product.id,
                'product_name': product.Short_Description,
                'reference': product.reference,
                'product_code': product.Barcode,
                'internal_product_code': product.Internal_Product_Code,
                'description': product.Short_Description,
                'category': product.Product_Group,
                'family_name': family_name,
                'family_id': family_id,
                'brand': family_name,  # Alias pour compatibilité
                'unit_of_measure': product.Stock_Unit,
                'is_active': product.Product_Status == 'ACTIVE',
                'is_variant': product.Is_Variant,
                'n_lot': product.n_lot,
                'n_serie': product.n_serie,
                'dlc': product.dlc,
                'numeros_serie': numeros_serie,
                'created_at': product.created_at.isoformat(),
                'updated_at': product.updated_at.isoformat()
            }
        except Exception as e:
            raise e
    
    def format_location_data(self, location):
        """Formate les données d'une location"""
        try:
            # Vérifier si warehouse existe via la chaîne: Location -> SousZone -> Zone -> Warehouse
            warehouse_name = None
            warehouse_id = None
            if location.sous_zone and location.sous_zone.zone and location.sous_zone.zone.warehouse:
                warehouse_name = location.sous_zone.zone.warehouse.warehouse_name
                warehouse_id = location.sous_zone.zone.warehouse.id
            
            # Vérifier si sous_zone existe
            sous_zone_name = None
            sous_zone_id = None
            if location.sous_zone:
                sous_zone_name = location.sous_zone.sous_zone_name
                sous_zone_id = location.sous_zone.id
            
            # Vérifier si zone existe
            zone_name = None
            zone_id = None
            if location.sous_zone and location.sous_zone.zone:
                zone_name = location.sous_zone.zone.zone_name
                zone_id = location.sous_zone.zone.id
            
            return {
                'web_id': location.id,
                'location_reference': location.location_reference,
                'location_name': location.location_reference,  # Utiliser location_reference comme nom
                'location_type': location.location_type.name if location.location_type else None,
                'location_type_id': location.location_type.id if location.location_type else None,
                'warehouse_name': warehouse_name,
                'warehouse_id': warehouse_id,
                'zone_name': zone_name,
                'zone_id': zone_id,
                'sous_zone_name': sous_zone_name,
                'sous_zone_id': sous_zone_id,
                'is_active': location.is_active,
                'created_at': location.created_at.isoformat(),
                'updated_at': location.updated_at.isoformat()
            }
        except Exception as e:
            raise e
    
    def format_stock_data(self, stock):
        """Formate les données d'un stock"""
        try:
            # Vérifier si location existe
            location_reference = None
            location_id = None
            if stock.location:
                location_reference = stock.location.location_reference
                location_id = stock.location.id
            
            # Vérifier si product existe
            product_name = None
            product_id = None
            if stock.product:
                product_name = stock.product.Short_Description
                product_id = stock.product.id
            
            # Vérifier si unit_of_measure existe
            unit_name = None
            unit_id = None
            if stock.unit_of_measure:
                unit_name = stock.unit_of_measure.name
                unit_id = stock.unit_of_measure.id
            
            # Vérifier si inventory existe
            inventory_reference = None
            inventory_id = None
            if stock.inventory:
                inventory_reference = stock.inventory.reference
                inventory_id = stock.inventory.id
            
            return {
                'web_id': stock.id,
                'reference': stock.reference,
                'location_reference': location_reference,
                'location_id': location_id,
                'product_name': product_name,
                'product_id': product_id,
                'quantity_available': stock.quantity_available,
                'quantity_reserved': stock.quantity_reserved,
                'quantity_in_transit': stock.quantity_in_transit,
                'quantity_in_receiving': stock.quantity_in_receiving,
                'unit_name': unit_name,
                'unit_id': unit_id,
                'inventory_reference': inventory_reference,
                'inventory_id': inventory_id,
                'created_at': stock.created_at.isoformat(),
                'updated_at': stock.updated_at.isoformat()
            }
        except Exception as e:
            raise e 