import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from django.db import transaction
from ..interfaces.stock_interface import IStockService
from ..repositories.stock_repository import StockRepository
from ..repositories import InventoryRepository
from apps.masterdata.models import Stock, Location, Product
from ..models import Inventory
from ..exceptions import InventoryNotFoundError, StockValidationError, StockNotFoundError
from apps.inventory.constants import InventoryType
import uuid

logger = logging.getLogger(__name__)

class StockService(IStockService):
    """Service pour la gestion des stocks."""
    
    def __init__(self, repository: StockRepository = None):
        self.repository = repository or StockRepository()
        self.inventory_repository = InventoryRepository()
    
    def import_stocks_from_excel(self, inventory_id: int, warehouse_id: int, excel_file) -> Dict[str, Any]:
        """
        Importe des stocks depuis un fichier Excel avec validation.
        
        Args:
            inventory_id: L'ID de l'inventaire
            warehouse_id: L'ID du magasin
            excel_file: Le fichier Excel à importer
            
        Returns:
            Dict[str, Any]: Résultat de l'import avec succès/erreurs
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            StockValidationError: Si le fichier est invalide
        """
        try:
            inventory = self.inventory_repository.get_by_id(inventory_id)
            location_required = inventory.inventory_type not in InventoryType.SINGLE_COUNTING

            df = self._read_excel_file(excel_file)
            self._normalize_excel_columns(df)
            self._validate_excel_structure(df, location_required=location_required)

            # Valider les emplacements fournis (ignoré s'il n'y en a aucun pour MAGASIN)
            self._validate_locations_belong_to_account_regroupement(
                df, inventory, location_required=location_required
            )

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
                    stock_data = self._row_to_stock_data(row, inventory_id)
                    validation_errors = self.validate_stock_data(
                        stock_data,
                        location_required=location_required,
                    )

                    if validation_errors:
                        results['errors'].append({
                            'row': row_number,
                            'errors': validation_errors,
                            'data': row.to_dict()
                        })
                        results['invalid_rows'] += 1
                    else:
                        clean_stock_data = {
                            'product': stock_data['product'],
                            'location': stock_data.get('location'),
                            'quantity_available': stock_data['quantity_available'],
                            'inventory_id': stock_data['inventory_id'],
                            'warehouse_id': warehouse_id,
                            'unit_of_measure': None,
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

            if results['invalid_rows'] > 0:
                results['success'] = False
                results['message'] = f"Import échoué: {results['invalid_rows']} lignes invalides"
                return results

            # Doublons dans le fichier
            seen = set()
            duplicates = []
            for idx, stock in enumerate(valid_stocks_data):
                location_id = stock['location'].id if stock['location'] else None
                key = (stock['product'].id, location_id, stock['inventory_id'])
                if key in seen:
                    duplicates.append(idx)
                else:
                    seen.add(key)
            if duplicates:
                results['success'] = False
                results['message'] = (
                    f"Import échoué: doublons détectés dans le fichier à la ligne(s) "
                    f"{', '.join(str(i+2) for i in duplicates)}"
                )
                return results

            if inventory.inventory_type in InventoryType.SINGLE_COUNTING:
                for stock in valid_stocks_data:
                    if Stock.objects.filter(
                        product=stock['product'],
                        location=stock['location'],
                        inventory_id=stock['inventory_id'],
                    ).exists():
                        location_label = (
                            stock['location'].location_reference
                            if stock['location']
                            else "sans emplacement"
                        )
                        results['success'] = False
                        results['message'] = (
                            f"Import échoué: un stock existe déjà pour le produit "
                            f"{stock['product']} ({location_label}) "
                            f"pour cet inventaire de type {inventory.inventory_type}."
                        )
                        return results

            for stock in valid_stocks_data:
                stock['reference'] = str(uuid.uuid4())[:20]

            if valid_stocks_data:
                with transaction.atomic():
                    deleted_count = self.repository.delete_by_inventory_id(inventory_id)
                    if deleted_count > 0:
                        logger.info(
                            f"Suppression de {deleted_count} stocks existants "
                            f"pour l'inventaire {inventory_id}"
                        )

                    try:
                        imported_stocks = self.repository.bulk_create(valid_stocks_data)
                    except Exception as e:
                        if "masterdata_stock_pkey" in str(e):
                            from django.db import connection
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    "SELECT setval('masterdata_stock_id_seq', "
                                    "(SELECT MAX(id) FROM masterdata_stock))"
                                )
                            imported_stocks = self.repository.bulk_create(valid_stocks_data)
                        else:
                            raise

                    results['imported_stocks'] = [
                        {
                            'id': stock.id,
                            'product': (
                                stock.product.Internal_Product_Code
                                if stock.product
                                else None
                            ),
                            'location': (
                                stock.location.location_reference
                                if stock.location
                                else None
                            ),
                            'quantity': stock.quantity_available
                        }
                        for stock in imported_stocks
                    ]

            logger.info(
                f"Import Excel terminé pour l'inventaire {inventory_id}: "
                f"{results['valid_rows']} stocks importés"
            )
            return results

        except InventoryNotFoundError:
            raise
        except StockValidationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'import Excel: {str(e)}", exc_info=True)
            raise StockValidationError(f"Erreur lors de l'import Excel: {str(e)}")

    def validate_stock_data(
        self,
        data: Dict[str, Any],
        location_required: bool = True,
    ) -> List[str]:
        """
        Valide les données d'un stock.

        Args:
            data: Les données du stock
            location_required: True pour GENERAL ; False pour MAGASIN/TOURNANT

        Returns:
            List[str]: Liste des erreurs de validation
        """
        errors = []

        if not data.get('product_reference'):
            errors.append("La référence du produit est obligatoire")
        else:
            try:
                product = Product.objects.get(
                    Internal_Product_Code=data['product_reference']
                )
                data['product'] = product
            except Product.DoesNotExist:
                errors.append(
                    f"Le produit avec la référence '{data['product_reference']}' "
                    f"n'existe pas"
                )

        location_reference = data.get('location_reference')
        if location_required and not location_reference:
            errors.append("La référence de l'emplacement est obligatoire")
        elif location_reference:
            try:
                location = Location.objects.get(
                    location_reference=location_reference
                )
                data['location'] = location
            except Location.DoesNotExist:
                errors.append(
                    f"L'emplacement avec la référence '{location_reference}' "
                    f"n'existe pas"
                )
        else:
            data['location'] = None

        quantity = data.get('quantity_available')
        if quantity is None:
            errors.append("La quantité est obligatoire")
        elif not isinstance(quantity, (int, float)) or quantity < 0:
            errors.append("La quantité doit être un nombre positif")

        if not data.get('inventory_id'):
            errors.append("L'ID de l'inventaire est obligatoire")

        return errors

    def create_stock(self, data: Dict[str, Any]) -> Stock:
        """Crée un nouveau stock."""
        return self.repository.create(data)
    
    def get_stocks_by_inventory(self, inventory_id: int) -> List[Stock]:
        """Récupère tous les stocks d'un inventaire."""
        return self.repository.get_by_inventory_id(inventory_id)
    
    def update_stock(self, stock_id: int, data: Dict[str, Any]) -> Stock:
        """Met à jour un stock existant."""
        return self.repository.update(stock_id, data)
    
    def delete_stock(self, stock_id: int) -> bool:
        """Supprime un stock."""
        return self.repository.delete(stock_id)
    
    def bulk_create_stocks(self, stocks_data: List[Dict[str, Any]]) -> List[Stock]:
        """Crée plusieurs stocks en lot."""
        return self.repository.bulk_create(stocks_data)
    
    def delete_stocks_by_inventory(self, inventory_id: int) -> int:
        """Supprime tous les stocks d'un inventaire."""
        return self.repository.delete_by_inventory_id(inventory_id)
    
    def _read_excel_file(self, excel_file) -> pd.DataFrame:
        """Lit le fichier Excel et retourne un DataFrame."""
        try:
            df = pd.read_excel(excel_file)
            return df
        except Exception as e:
            raise StockValidationError(f"Impossible de lire le fichier Excel: {str(e)}")

    def _normalize_excel_columns(self, df: pd.DataFrame) -> None:
        """Normalise les noms de colonnes (minuscules, trim)."""
        df.columns = df.columns.astype(str).str.strip().str.lower()

    def _validate_excel_structure(
        self,
        df: pd.DataFrame,
        location_required: bool = True,
    ) -> None:
        """
        Valide la structure du fichier Excel.

        GENERAL : article, emplacement, quantite obligatoires.
        MAGASIN / TOURNANT : article, quantite obligatoires ; emplacement optionnel.
        """
        required_columns = ['article', 'quantite']
        if location_required:
            required_columns.insert(1, 'emplacement')

        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise StockValidationError(
                f"Colonnes manquantes dans le fichier Excel: {', '.join(missing_columns)}. "
                f"Colonnes requises: {', '.join(required_columns)}"
            )

        if df.empty:
            raise StockValidationError("Le fichier Excel est vide")

    def _extract_excel_locations(self, df: pd.DataFrame) -> set:
        """Retourne les emplacements non vides présents dans le fichier."""
        if 'emplacement' not in df.columns:
            return set()
        locations = set()
        for value in df['emplacement'].tolist():
            if pd.isna(value):
                continue
            text = str(value).strip()
            if text and text.lower() != 'nan':
                locations.add(text)
        return locations

    def _validate_locations_belong_to_account_regroupement(
        self,
        df: pd.DataFrame,
        inventory: Inventory,
        location_required: bool = True,
    ) -> None:
        """
        Valide que les emplacements du fichier appartiennent au regroupement du compte.

        Pour MAGASIN / TOURNANT : si aucune valeur d'emplacement n'est fournie,
        la validation est ignorée.
        """
        from apps.masterdata.models import RegroupementEmplacement, Location

        excel_locations = self._extract_excel_locations(df)
        if not excel_locations:
            if location_required:
                raise StockValidationError(
                    "Aucun emplacement renseigné dans le fichier Excel."
                )
            logger.info(
                "Aucun emplacement fourni — validation regroupement ignorée "
                "(MAGASIN/TOURNANT)."
            )
            return

        account_links = inventory.awi_links.all()
        if not account_links.exists():
            raise StockValidationError("Aucun compte lié à cet inventaire.")

        account = account_links.first().account

        regroupement = RegroupementEmplacement.objects.filter(account=account).first()
        if not regroupement:
            raise StockValidationError(
                f"Aucun regroupement d'emplacement trouvé pour le compte "
                f"'{account.account_name}'."
            )

        regroupement_locations = set(Location.objects.filter(
            regroupement=regroupement,
            is_active=True
        ).values_list('location_reference', flat=True))

        if not regroupement_locations:
            raise StockValidationError(
                f"Aucun emplacement actif trouvé dans le regroupement "
                f"'{regroupement.nom}' du compte '{account.account_name}'."
            )

        invalid_locations = excel_locations - regroupement_locations
        if invalid_locations:
            raise StockValidationError(
                f"Les emplacements suivants ne font pas partie du regroupement "
                f"'{regroupement.nom}' du compte '{account.account_name}': "
                f"{', '.join(sorted(invalid_locations))}"
            )

        logger.info(
            f"Validation des emplacements réussie: "
            f"{len(excel_locations)} emplacements valides trouvés"
        )

    def _normalize_optional_text(self, value: Any) -> Optional[str]:
        """Normalise une cellule Excel optionnelle en str ou None."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if pd.isna(value):
            return None
        text = str(value).strip()
        if not text or text.lower() == 'nan':
            return None
        return text

    def _row_to_stock_data(self, row: pd.Series, inventory_id: int) -> Dict[str, Any]:
        """Convertit une ligne Excel en données de stock."""
        location_value = row['emplacement'] if 'emplacement' in row.index else None
        return {
            'product_reference': self._normalize_optional_text(row.get('article')),
            'location_reference': self._normalize_optional_text(location_value),
            'quantity_available': (
                float(row['quantite']) if pd.notna(row['quantite']) else 0
            ),
            'inventory_id': inventory_id
        }
