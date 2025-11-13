import os
import pandas as pd
from django.db import transaction
from import_export import resources, exceptions
from ..models import ImportTask, ImportError, Product, Family
import logging
from datetime import datetime
import tempfile

logger = logging.getLogger(__name__)


class ProductImportService:
    """Service pour importer des produits en mode 'tout ou rien'"""
    
    CHUNK_SIZE = 10000  # 10k lignes par chunk
    
    def __init__(self, resource_class):
        self.resource_class = resource_class
        self.family_cache = {}
        self._load_family_cache()
    
    def _load_family_cache(self):
        """Charge toutes les familles en mémoire"""
        self.family_cache = {
            f.family_name: f 
            for f in Family.objects.only('id', 'family_name')
        }
        logger.info(f"Cache de {len(self.family_cache)} familles chargé")
    
    def process_file_chunked(self, file_path: str, import_task: ImportTask):
        """
        Traite un fichier en mode 'tout ou rien'
        
        LOGIQUE:
        1. Valide TOUTES les lignes AVANT d'importer
        2. Détecte les doublons DANS le fichier
        3. Si une seule erreur → ANNULER (aucun import)
        4. Si toutes valides → Importer TOUT dans une transaction
        5. Si erreur pendant import → Rollback automatique
        """
        try:
            # PHASE 1: VALIDATION COMPLÈTE
            import_task.status = 'VALIDATING'
            import_task.save()
            
            total_rows = self._count_file_rows(file_path)
            import_task.total_rows = total_rows
            import_task.save()
            
            logger.info(f"Début validation complète ({total_rows} lignes)")
            
            # Lire le fichier Excel complet
            df_full = pd.read_excel(file_path, engine='openpyxl')
            
            # PHASE 1.1: Détecter les doublons DANS le fichier
            duplicate_errors = self._detect_duplicates_in_file(df_full)
            validation_errors = []
            
            # Convertir les erreurs de doublons en ImportError
            for dup_error in duplicate_errors:
                error_obj = ImportError(
                    import_task=import_task,
                    row_number=dup_error['row_number'],
                    error_type=dup_error['error_type'],
                    error_message=dup_error['error_message'],
                    field_name=dup_error.get('field_name'),
                    field_value=dup_error.get('field_value'),
                    row_data=dup_error.get('row_data', {}),
                )
                validation_errors.append(error_obj)
            
            # PHASE 1.2: Valider toutes les lignes (traiter par chunks)
            row_number = 2  # Ligne 1 = header
            for i in range(0, len(df_full), self.CHUNK_SIZE):
                chunk_df = df_full.iloc[i:i + self.CHUNK_SIZE]
                chunk_errors = self._validate_chunk(chunk_df, import_task, row_number)
                validation_errors.extend(chunk_errors)
                
                import_task.validated_rows = min(row_number + len(chunk_df) - 1, total_rows)
                import_task.save()
                
                row_number += len(chunk_df)
            
            # VÉRIFICATION: Si erreurs → ANNULER TOUT
            if validation_errors:
                import_task.status = 'CANCELLED'
                import_task.error_count = len(validation_errors)
                import_task.error_message = (
                    f"Import annulé: {len(validation_errors)} erreur(s) détectée(s) "
                    f"lors de la validation. Aucun produit n'a été importé."
                )
                
                # Sauvegarder les erreurs
                ImportError.objects.bulk_create(validation_errors, batch_size=1000)
                
                # Générer fichier d'erreurs
                errors_file_path = self._generate_errors_file(import_task, validation_errors)
                import_task.errors_file_path = errors_file_path
                import_task.save()
                
                logger.warning(f"Import annulé: {len(validation_errors)} erreurs détectées")
                return  # ⭐ ARRÊT: Rien n'est importé
            
            # PHASE 2: IMPORT (seulement si validation OK)
            logger.info("Validation OK, début import dans transaction")
            import_task.status = 'PROCESSING'
            import_task.save()
            
            # ⭐ IMPORT DANS UNE TRANSACTION (tout ou rien)
            try:
                with transaction.atomic():  # Transaction globale
                    total_imported = 0
                    total_updated = 0
                    
                    row_number = 2
                    # Lire le fichier Excel et traiter par chunks
                    df_full = pd.read_excel(file_path, engine='openpyxl')
                    
                    # Traiter par chunks
                    for i in range(0, len(df_full), self.CHUNK_SIZE):
                        chunk_df = df_full.iloc[i:i + self.CHUNK_SIZE]
                        chunk_data = self._dataframe_to_dataset(chunk_df)
                        
                        result = self._import_chunk(chunk_data, import_task, row_number)
                        
                        total_imported += result.get('imported', 0)
                        total_updated += result.get('updated', 0)
                        
                        import_task.processed_rows = min(row_number + len(chunk_df) - 1, total_rows)
                        import_task.imported_count = total_imported
                        import_task.updated_count = total_updated
                        import_task.save()
                        
                        row_number += len(chunk_df)
                    
                    # Succès complet
                    import_task.status = 'COMPLETED'
                    import_task.processed_rows = total_rows
                    import_task.save()
                    
                    logger.info(
                        f"Import terminé avec succès: {total_imported} importés, "
                        f"{total_updated} mis à jour"
                    )
                    
            except Exception as e:
                # ⭐ Erreur pendant import → rollback automatique
                import_task.status = 'FAILED'
                import_task.error_message = (
                    f"Erreur lors de l'import: {str(e)}. "
                    f"Aucun produit n'a été importé (rollback automatique)."
                )
                import_task.save()
                logger.error(f"Erreur import (rollback): {str(e)}", exc_info=True)
                raise  # Transaction annulée automatiquement
            
        except Exception as e:
            if import_task.status not in ['CANCELLED', 'FAILED']:
                import_task.status = 'FAILED'
                import_task.error_message = str(e)
                import_task.save()
            logger.error(f"Erreur import: {str(e)}", exc_info=True)
            raise
    
    def _detect_duplicates_in_file(self, df: pd.DataFrame) -> list:
        """Détecte les doublons dans le fichier Excel lui-même"""
        errors = []
        
        # Normaliser les colonnes (gérer les variations de casse et espaces)
        df.columns = df.columns.str.strip().str.lower()
        
        # Vérifier les doublons de Internal_Product_Code dans le fichier
        if 'internal product code' in df.columns:
            internal_code_col = 'internal product code'
            df[internal_code_col] = df[internal_code_col].astype(str).str.strip()
            
            # Trouver tous les codes dupliqués
            value_counts = df[internal_code_col].value_counts()
            duplicates = value_counts[value_counts > 1].index.tolist()
            
            for internal_code in duplicates:
                if internal_code and internal_code != 'nan' and internal_code.lower() != 'nan':
                    # Trouver toutes les lignes avec ce code
                    duplicate_indices = df[df[internal_code_col] == internal_code].index.tolist()
                    row_numbers = [r + 2 for r in duplicate_indices]  # +2 car ligne 1 = header, index 0-based
                    
                    # Créer une erreur pour chaque ligne dupliquée
                    for idx in duplicate_indices:
                        row = df.iloc[idx]
                        errors.append({
                            'row_number': idx + 2,
                            'error_type': 'DUPLICATE_ERROR',
                            'error_message': f"Le code produit interne '{internal_code}' apparaît plusieurs fois dans le fichier (lignes: {', '.join(map(str, row_numbers))}).",
                            'field_name': 'internal product code',
                            'field_value': internal_code,
                            'row_data': row.to_dict(),
                        })
        
        # Vérifier les doublons de Barcode dans le fichier (si présent et non vide)
        if 'barcode' in df.columns:
            barcode_col = 'barcode'
            df[barcode_col] = df[barcode_col].astype(str).str.strip()
            # Filtrer les valeurs vides et 'nan'
            df_barcode = df[(df[barcode_col] != '') & (df[barcode_col] != 'nan') & (df[barcode_col].notna())]
            
            # Trouver tous les barcodes dupliqués
            if not df_barcode.empty:
                value_counts = df_barcode[barcode_col].value_counts()
                duplicates = value_counts[value_counts > 1].index.tolist()
                
                for barcode in duplicates:
                    if barcode and barcode != 'nan' and barcode.lower() != 'nan':
                        # Trouver toutes les lignes avec ce barcode
                        duplicate_indices = df_barcode[df_barcode[barcode_col] == barcode].index.tolist()
                        row_numbers = [r + 2 for r in duplicate_indices]
                        
                        # Créer une erreur pour chaque ligne dupliquée
                        for idx in duplicate_indices:
                            row = df_barcode.iloc[idx]
                            errors.append({
                                'row_number': idx + 2,
                                'error_type': 'DUPLICATE_ERROR',
                                'error_message': f"Le code-barres '{barcode}' apparaît plusieurs fois dans le fichier (lignes: {', '.join(map(str, row_numbers))}).",
                                'field_name': 'barcode',
                                'field_value': barcode,
                                'row_data': row.to_dict(),
                            })
        
        return errors
    
    def _validate_chunk(self, df: pd.DataFrame, import_task: ImportTask, start_row: int) -> list:
        """Valide un chunk et retourne la liste des erreurs"""
        errors = []
        
        for index, row_data in df.iterrows():
            row_number = start_row + index
            row_dict = row_data.to_dict()
            
            validation_error = self._validate_row(row_dict, row_number)
            if validation_error:
                # Si c'est un dict d'erreur (format standard)
                if isinstance(validation_error, dict):
                    error_obj = ImportError(
                        import_task=import_task,
                        row_number=row_number,
                        error_type=validation_error['error_type'],
                        error_message=validation_error['error_message'],
                        field_name=validation_error.get('field_name'),
                        field_value=validation_error.get('field_value'),
                        row_data=row_dict,
                    )
                    errors.append(error_obj)
                # Si c'est déjà un ImportError (depuis _detect_duplicates_in_file)
                elif hasattr(validation_error, 'row_number'):
                    validation_error.import_task = import_task
                    errors.append(validation_error)
        
        return errors
    
    def _validate_row(self, row_data: dict, row_number: int) -> dict:
        """Valide une ligne et retourne un dict d'erreur si invalide"""
        # Validation famille
        family_name = str(row_data.get('product family', '')).strip()
        if not family_name:
            return {
                'error_type': 'VALIDATION_ERROR',
                'error_message': "La colonne 'product family' est obligatoire.",
                'field_name': 'product family',
                'field_value': family_name,
            }
        
        if family_name not in self.family_cache:
            return {
                'error_type': 'VALIDATION_ERROR',
                'error_message': f"La famille '{family_name}' n'existe pas dans la base de données.",
                'field_name': 'product family',
                'field_value': family_name,
            }
        
        # Validation barcode
        barcode = str(row_data.get('barcode', '')).strip()
        if not barcode:
            return {
                'error_type': 'VALIDATION_ERROR',
                'error_message': "La colonne 'barcode' est obligatoire.",
                'field_name': 'barcode',
                'field_value': barcode,
            }
        
        # Validation code produit interne
        internal_code = str(row_data.get('internal product code', '')).strip()
        if not internal_code:
            return {
                'error_type': 'VALIDATION_ERROR',
                'error_message': "La colonne 'internal product code' est obligatoire.",
                'field_name': 'internal product code',
                'field_value': internal_code,
            }
        
        # Vérifier unicité code produit interne dans la base de données
        if Product.objects.filter(Internal_Product_Code=internal_code).exists():
            return {
                'error_type': 'VALIDATION_ERROR',
                'error_message': f"Le code produit interne '{internal_code}' existe déjà dans la base de données.",
                'field_name': 'internal product code',
                'field_value': internal_code,
            }
        
        # Vérifier unicité barcode dans la base de données (si présent)
        if barcode:
            existing_product = Product.objects.filter(Barcode=barcode).first()
            if existing_product:
                return {
                    'error_type': 'VALIDATION_ERROR',
                    'error_message': f"Le code-barres '{barcode}' existe déjà dans la base de données (produit: {existing_product.Short_Description}).",
                    'field_name': 'barcode',
                    'field_value': barcode,
                }
        
        # Validation description
        short_desc = str(row_data.get('short description', '')).strip()
        if not short_desc:
            return {
                'error_type': 'VALIDATION_ERROR',
                'error_message': "La colonne 'short description' est obligatoire.",
                'field_name': 'short description',
                'field_value': short_desc,
            }
        
        # Validation unité de stock
        stock_unit = str(row_data.get('stock unit', '')).strip()
        if not stock_unit:
            return {
                'error_type': 'VALIDATION_ERROR',
                'error_message': "La colonne 'stock unit' est obligatoire.",
                'field_name': 'stock unit',
                'field_value': stock_unit,
            }
        
        return None  # Pas d'erreur
    
    def _import_chunk(self, dataset, import_task: ImportTask, start_row: int):
        """Importe un chunk dans la transaction"""
        resource = self.resource_class()
        imported = 0
        updated = 0
        
        for index, row_data in enumerate(dataset.dict):
            try:
                single_row_dataset = type(dataset)()
                single_row_dataset.dict = [row_data]
                
                result = resource.import_data(
                    single_row_dataset,
                    dry_run=False,
                    raise_errors=True,  # ⭐ Lever exception si erreur
                    use_transactions=False,  # Transaction gérée au niveau supérieur
                )
                
                if result.totals.get('new', 0) > 0:
                    imported += 1
                elif result.totals.get('update', 0) > 0:
                    updated += 1
                
            except Exception as e:
                # ⭐ Toute erreur annule la transaction
                logger.error(f"Erreur ligne {start_row + index}: {str(e)}")
                raise exceptions.ImportError(
                    f"Erreur ligne {start_row + index}: {str(e)}"
                )
        
        return {
            'imported': imported,
            'updated': updated,
        }
    
    def _count_file_rows(self, file_path: str) -> int:
        """Compte le nombre de lignes dans le fichier"""
        try:
            # Lire uniquement pour compter les lignes (sans charger toutes les données)
            df = pd.read_excel(file_path, engine='openpyxl', nrows=0)  # Lire seulement les headers
            # Utiliser openpyxl directement pour compter les lignes sans charger tout en mémoire
            from openpyxl import load_workbook
            wb = load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active
            # Compter les lignes non vides (sans la ligne d'en-tête)
            row_count = sum(1 for row in ws.iter_rows(min_row=2) if any(cell.value for cell in row))
            wb.close()
            return row_count
        except Exception as e:
            logger.warning(f"Impossible de compter les lignes avec openpyxl, tentative avec pandas: {str(e)}")
            try:
                # Fallback: lire le fichier complet (peut être lent pour gros fichiers)
                df = pd.read_excel(file_path, engine='openpyxl')
                return len(df)
            except Exception as e2:
                logger.error(f"Impossible de compter les lignes: {str(e2)}")
                return 0
    
    def _dataframe_to_dataset(self, df):
        """Convertit un DataFrame pandas en Dataset import_export"""
        from tablib import Dataset
        
        # Convertir DataFrame en liste de dictionnaires
        records = df.to_dict('records')
        
        # Créer le Dataset avec les en-têtes et les données
        if len(records) > 0:
            dataset = Dataset()
            # Définir les en-têtes depuis les clés du premier enregistrement
            dataset.headers = list(records[0].keys())
            # Ajouter les données
            for record in records:
                dataset.append([record.get(header, '') for header in dataset.headers])
        else:
            dataset = Dataset()
        
        return dataset
    
    def _generate_errors_file(self, import_task: ImportTask, errors: list) -> str:
        """Génère un fichier Excel avec toutes les erreurs"""
        error_data = []
        for error in errors:
            error_data.append({
                'Ligne': error.row_number,
                'Type d\'erreur': error.error_type,
                'Champ concerné': error.field_name or '',
                'Valeur du champ': str(error.field_value) if error.field_value else '',
                'Message d\'erreur': error.error_message,
                'Barcode': error.row_data.get('barcode', ''),
                'Code produit interne': error.row_data.get('internal product code', ''),
                'Description': error.row_data.get('short description', ''),
            })
        
        df_errors = pd.DataFrame(error_data)
        
        temp_dir = tempfile.gettempdir()
        errors_file_path = os.path.join(
            temp_dir,
            f'errors_import_{import_task.id}_{int(datetime.now().timestamp())}.xlsx'
        )
        
        df_errors.to_excel(errors_file_path, index=False, engine='openpyxl')
        logger.info(f"Fichier d'erreurs généré: {errors_file_path}")
        return errors_file_path
