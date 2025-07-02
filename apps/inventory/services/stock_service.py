import pandas as pd
import logging
from typing import List, Dict, Any
from django.db import transaction
from ..interfaces.stock_interface import IStockService
from ..repositories.stock_repository import StockRepository
from ..repositories import InventoryRepository
from apps.masterdata.models import Stock, Location, Product, UnitOfMeasure
from ..exceptions import InventoryNotFoundError, StockValidationError, StockNotFoundError

logger = logging.getLogger(__name__)

class StockService(IStockService):
    """Service pour la gestion des stocks."""
    
    def __init__(self, repository: StockRepository = None):
        self.repository = repository or StockRepository()
        self.inventory_repository = InventoryRepository()
    
    def import_stocks_from_excel(self, inventory_id: int, excel_file) -> Dict[str, Any]:
        """
        Importe des stocks depuis un fichier Excel avec validation.
        
        Args:
            inventory_id: L'ID de l'inventaire
            excel_file: Le fichier Excel à importer
            
        Returns:
            Dict[str, Any]: Résultat de l'import avec succès/erreurs
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            StockValidationError: Si le fichier est invalide
        """
        try:
            # Vérifier que l'inventaire existe
            inventory = self.inventory_repository.get_by_id(inventory_id)
            
            # Lire le fichier Excel
            df = self._read_excel_file(excel_file)
            
            # Valider la structure du fichier
            self._validate_excel_structure(df)
            
            # Traiter chaque ligne
            results = {
                'success': True,
                'message': 'Import terminé avec succès',
                'total_rows': len(df),
                'valid_rows': 0,
                'invalid_rows': 0,
                'errors': [],
                'imported_stocks': []
            }
            
            valid_stocks_data = []
            
            for index, row in df.iterrows():
                row_number = index + 2  # +2 car Excel commence à 1 et on a un header
                
                try:
                    # Convertir la ligne en dictionnaire
                    stock_data = self._row_to_stock_data(row, inventory_id)
                    
                    # Valider les données
                    validation_errors = self.validate_stock_data(stock_data)
                    
                    if validation_errors:
                        results['errors'].append({
                            'row': row_number,
                            'errors': validation_errors,
                            'data': row.to_dict()
                        })
                        results['invalid_rows'] += 1
                    else:
                        # Nettoyer les données pour le repository (supprimer les champs de référence)
                        clean_stock_data = {
                            'product': stock_data['product'],
                            'location': stock_data['location'],
                            'quantity_available': stock_data['quantity_available'],
                            'inventory_id': stock_data['inventory_id'],
                            'unit_of_measure': UnitOfMeasure.objects.get(id=4)  # Valeur par défaut
                        }
                        valid_stocks_data.append(clean_stock_data)
                        results['valid_rows'] += 1
                        
                except Exception as e:
                    results['errors'].append({
                        'row': row_number,
                        'errors': [f"Erreur de traitement: {str(e)}"],
                        'data': row.to_dict()
                    })
                    results['invalid_rows'] += 1
            
            # Si des erreurs, ne pas importer
            if results['invalid_rows'] > 0:
                results['success'] = False
                results['message'] = f"Import échoué: {results['invalid_rows']} lignes invalides"
                return results
            
            # Importer les stocks valides
            if valid_stocks_data:
                with transaction.atomic():
                    # Supprimer les anciens stocks de cet inventaire
                    self.repository.delete_by_inventory_id(inventory_id)
                    
                    # Créer les nouveaux stocks
                    try:
                        imported_stocks = self.repository.bulk_create(valid_stocks_data)
                    except Exception as e:
                        # Si erreur de contrainte unique sur l'ID, réinitialiser la séquence
                        if "masterdata_stock_pkey" in str(e):
                            from django.db import connection
                            with connection.cursor() as cursor:
                                cursor.execute("SELECT setval('masterdata_stock_id_seq', (SELECT MAX(id) FROM masterdata_stock))")
                            # Réessayer la création
                            imported_stocks = self.repository.bulk_create(valid_stocks_data)
                        else:
                            raise
                    
                    results['imported_stocks'] = [
                        {
                            'id': stock.id,
                            'product': stock.product.product_name if stock.product else None,
                            'location': stock.location.location_name if stock.location else None,
                            'quantity': stock.quantity_available
                        }
                        for stock in imported_stocks
                    ]
            
            logger.info(f"Import Excel terminé pour l'inventaire {inventory_id}: {results['valid_rows']} stocks importés")
            return results
            
        except InventoryNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'import Excel: {str(e)}", exc_info=True)
            raise StockValidationError(f"Erreur lors de l'import Excel: {str(e)}")
    
    def validate_stock_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Valide les données d'un stock.
        
        Args:
            data: Les données du stock
            
        Returns:
            List[str]: Liste des erreurs de validation
        """
        errors = []
        
        # Validation du produit par référence
        if not data.get('product_reference'):
            errors.append("La référence du produit est obligatoire")
        else:
            try:
                product = Product.objects.get(Internal_Product_Code=data['product_reference'])
                data['product'] = product  # Utiliser 'product' pour le modèle Stock
            except Product.DoesNotExist:
                errors.append(f"Le produit avec la référence '{data['product_reference']}' n'existe pas")
        
        # Validation de l'emplacement par référence
        if not data.get('location_reference'):
            errors.append("La référence de l'emplacement est obligatoire")
        else:
            try:
                location = Location.objects.get(location_reference=data['location_reference'])
                data['location'] = location  # Utiliser 'location' pour le modèle Stock
            except Location.DoesNotExist:
                errors.append(f"L'emplacement avec la référence '{data['location_reference']}' n'existe pas")
        
        # Validation de la quantité
        quantity = data.get('quantity_available')
        if quantity is None:
            errors.append("La quantité est obligatoire")
        elif not isinstance(quantity, (int, float)) or quantity < 0:
            errors.append("La quantité doit être un nombre positif")
        
        # Validation de l'inventaire
        if not data.get('inventory_id'):
            errors.append("L'ID de l'inventaire est obligatoire")
        
        return errors
    
    def create_stock(self, data: Dict[str, Any]) -> Stock:
        """
        Crée un nouveau stock.
        
        Args:
            data: Les données du stock
            
        Returns:
            Stock: Le stock créé
        """
        return self.repository.create(data)
    
    def get_stocks_by_inventory(self, inventory_id: int) -> List[Stock]:
        """
        Récupère tous les stocks d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            List[Stock]: Liste des stocks de l'inventaire
        """
        return self.repository.get_by_inventory_id(inventory_id)
    
    def update_stock(self, stock_id: int, data: Dict[str, Any]) -> Stock:
        """
        Met à jour un stock existant.
        
        Args:
            stock_id: L'ID du stock
            data: Les nouvelles données du stock
            
        Returns:
            Stock: Le stock mis à jour
        """
        return self.repository.update(stock_id, data)
    
    def delete_stock(self, stock_id: int) -> bool:
        """
        Supprime un stock.
        
        Args:
            stock_id: L'ID du stock
            
        Returns:
            bool: True si la suppression a réussi
        """
        return self.repository.delete(stock_id)
    
    def bulk_create_stocks(self, stocks_data: List[Dict[str, Any]]) -> List[Stock]:
        """
        Crée plusieurs stocks en lot.
        
        Args:
            stocks_data: Liste des données des stocks
            
        Returns:
            List[Stock]: Liste des stocks créés
        """
        return self.repository.bulk_create(stocks_data)
    
    def delete_stocks_by_inventory(self, inventory_id: int) -> bool:
        """
        Supprime tous les stocks d'un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            bool: True si la suppression a réussi
        """
        return self.repository.delete_by_inventory_id(inventory_id)
    
    def _read_excel_file(self, excel_file) -> pd.DataFrame:
        """
        Lit le fichier Excel et retourne un DataFrame.
        
        Args:
            excel_file: Le fichier Excel
            
        Returns:
            pd.DataFrame: Les données du fichier Excel
        """
        try:
            df = pd.read_excel(excel_file)
            return df
        except Exception as e:
            raise StockValidationError(f"Impossible de lire le fichier Excel: {str(e)}")
    
    def _validate_excel_structure(self, df: pd.DataFrame) -> None:
        """
        Valide la structure du fichier Excel.
        
        Args:
            df: Le DataFrame du fichier Excel
            
        Raises:
            StockValidationError: Si la structure est invalide
        """
        required_columns = ['article', 'emplacement', 'quantite']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise StockValidationError(
                f"Colonnes manquantes dans le fichier Excel: {', '.join(missing_columns)}. "
                f"Colonnes requises: {', '.join(required_columns)}"
            )
        
        if df.empty:
            raise StockValidationError("Le fichier Excel est vide")
    
    def _row_to_stock_data(self, row: pd.Series, inventory_id: int) -> Dict[str, Any]:
        """
        Convertit une ligne Excel en données de stock.
        
        Args:
            row: La ligne Excel
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Dict[str, Any]: Les données du stock
        """
        return {
            'product_reference': str(row['article']) if pd.notna(row['article']) else None,
            'location_reference': str(row['emplacement']) if pd.notna(row['emplacement']) else None,
            'quantity_available': float(row['quantite']) if pd.notna(row['quantite']) else 0,
            'inventory_id': inventory_id
        } 