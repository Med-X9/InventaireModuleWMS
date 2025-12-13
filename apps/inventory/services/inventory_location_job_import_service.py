"""
Service pour l'import asynchrone des InventoryLocationJob depuis un fichier Excel
"""
import pandas as pd
import re
import logging
import threading
from typing import Dict, List, Any, Optional
from django.db import transaction
from django.utils import timezone
from apps.inventory.models import Inventory, Setting, Job, JobDetail, Counting
from apps.masterdata.models import Warehouse, Location, InventoryLocationJob
from apps.inventory.repositories.inventory_location_job_repository import InventoryLocationJobRepository
from apps.masterdata.repositories.warehouse_repository import WarehouseRepository
from apps.masterdata.repositories.location_repository import LocationRepository
from apps.masterdata.exceptions import InventoryLocationJobValidationError
from apps.inventory.repositories.inventory_repository import InventoryRepository

logger = logging.getLogger(__name__)


class InventoryLocationJobImportService:
    """
    Service pour importer des InventoryLocationJob depuis un fichier Excel
    avec validation complète et traitement asynchrone
    """
    
    def __init__(self):
        self.repository = InventoryLocationJobRepository()
        self.warehouse_repo = WarehouseRepository()
        self.location_repo = LocationRepository()
        self.inventory_repo = InventoryRepository()
    
    def import_from_excel_async(
        self,
        inventory_id: int,
        file_path: str,
        callback: Optional[callable] = None
    ) -> None:
        """
        Lance l'import de manière asynchrone dans un thread séparé
        
        Args:
            inventory_id: ID de l'inventaire
            file_path: Chemin vers le fichier Excel
            callback: Fonction de callback appelée avec le résultat (optionnel)
        """
        def import_task():
            try:
                result = self.import_from_excel(inventory_id, file_path)
                if callback:
                    callback(result)
            except Exception as e:
                logger.error(f"Erreur lors de l'import asynchrone: {str(e)}", exc_info=True)
                if callback:
                    callback({
                        'success': False,
                        'message': f"Erreur lors de l'import: {str(e)}",
                        'errors': []
                    })
        
        thread = threading.Thread(target=import_task, daemon=True)
        thread.start()
        logger.info(f"Import asynchrone lancé pour l'inventaire {inventory_id}")
    
    def import_from_excel(self, inventory_id: int, file_path: str) -> Dict[str, Any]:
        """
        Importe les données depuis un fichier Excel avec validation complète
        
        Args:
            inventory_id: ID de l'inventaire
            file_path: Chemin vers le fichier Excel
            
        Returns:
            Dict contenant le résultat de l'import (success, message, errors, imported_count)
            
        Raises:
            InventoryLocationJobValidationError: Si des erreurs de validation sont détectées
        """
        try:
            # Vérifier que l'inventaire existe
            inventory = self.inventory_repo.get_by_id(inventory_id)
            
            # Lire le fichier Excel
            logger.info(f"Lecture du fichier Excel: {file_path}")
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Normaliser les noms de colonnes (minuscules, sans espaces)
            df.columns = df.columns.str.strip().str.lower()
            
            # Valider la structure du fichier
            self._validate_excel_structure(df)
            
            # Valider toutes les lignes AVANT toute insertion
            validation_errors = []
            validated_data = []
            
            for index, row in df.iterrows():
                row_number = index + 2  # +2 car ligne 1 = header, index 0-based
                row_dict = row.to_dict()
                
                # Valider la ligne
                errors = self._validate_row(
                    row_dict=row_dict,
                    row_number=row_number,
                    inventory=inventory
                )
                
                if errors:
                    validation_errors.extend(errors)
                else:
                    # Extraire le numéro du job pour la validation d'incrémentation
                    job_value = str(row_dict.get('job', '')).strip()
                    job_number = None
                    if job_value:
                        job_pattern = r'^job-(\d+)$'
                        match = re.match(job_pattern, job_value, re.IGNORECASE)
                        if match:
                            job_number = int(match.group(1))
                    
                    # Préparer les données pour l'insertion
                    # Si active = false, on peut avoir job et sessions vides
                    is_active = row_dict.get('is_active', False)
                    validated_data.append({
                        'inventaire_id': inventory_id,
                        'warehouse_id': row_dict.get('warehouse_id'),  # Pour la création des jobs
                        'emplacement_id': row_dict.get('emplacement_id'),
                        'job': job_value if job_value else None,  # Job peut être None si active = false
                        'job_number': job_number,  # Pour la validation d'incrémentation
                        'is_active': is_active,  # Pour la validation d'incrémentation
                        'active_excel': is_active,  # Pour la synchronisation avec Location.is_active
                        'session_1': str(row_dict.get('session_1', '')).strip() if pd.notna(row_dict.get('session_1')) and str(row_dict.get('session_1', '')).strip() else None,
                        'session_2': str(row_dict.get('session_2', '')).strip() if pd.notna(row_dict.get('session_2')) and str(row_dict.get('session_2', '')).strip() else None,
                    })
            
            # Si des erreurs de validation, ne rien insérer
            if validation_errors:
                logger.warning(f"Import annulé: {len(validation_errors)} erreur(s) détectée(s)")
                return {
                    'success': False,
                    'message': f"Import annulé: {len(validation_errors)} erreur(s) détectée(s)",
                    'errors': validation_errors,
                    'imported_count': 0
                }
            
            # Valider l'incrémentation des jobs
            job_errors = self._validate_job_increment(validated_data)
            if job_errors:
                logger.warning(f"Import annulé: erreur(s) d'incrémentation des jobs")
                return {
                    'success': False,
                    'message': f"Import annulé: erreur(s) d'incrémentation des jobs",
                    'errors': job_errors,
                    'imported_count': 0
                }
            
            # Si toutes les validations passent, procéder à la synchronisation puis à l'insertion
            with transaction.atomic():
                # 6. D'abord, synchroniser le champ active du fichier Excel avec Location.is_active
                # Cette étape s'exécute AVANT l'insertion dans InventoryLocationJob
                # Le champ active du fichier Excel sert uniquement à la synchronisation, pas à l'insertion
                sync_result = self._sync_location_active_status(validated_data)
                logger.info(f"Synchronisation des emplacements: {sync_result['updated_count']} emplacement(s) mis à jour")
                
                # 7. Ensuite, insérer dans InventoryLocationJob
                # Supprimer les anciens enregistrements pour cet inventaire
                self.repository.delete_by_inventory_id(inventory_id)
                
                # Préparer les données pour l'insertion
                # Champs à insérer : inventaire, emplacement, job, session_1, session_2
                # Champs à EXCLURE : 
                #   - active_excel (utilisé uniquement pour la synchronisation de Location.is_active)
                #   - job_number (utilisé uniquement pour la validation d'incrémentation)
                #   - is_active (utilisé uniquement pour la validation conditionnelle)
                #   - warehouse_id (le warehouse sert uniquement à la validation, pas à l'insertion)
                data_to_insert = [
                    {
                        'inventaire_id': data['inventaire_id'],
                        'emplacement_id': data['emplacement_id'],
                        'job': data['job'],
                        'session_1': data['session_1'],
                        'session_2': data['session_2'],
                    }
                    for data in validated_data
                ]
                
                # Créer les nouveaux enregistrements dans InventoryLocationJob
                created_objects = self.repository.bulk_create(data_to_insert)
                
                logger.info(f"Import réussi: {len(created_objects)} enregistrement(s) créé(s) dans InventoryLocationJob")
                
                # 9. Créer automatiquement les Jobs et JobDetails à partir des données importées
                # Cette étape s'exécute uniquement si toutes les étapes précédentes sont réussies
                # Elle est dans la transaction atomique pour garantir la cohérence
                jobs_result = self._create_jobs_and_details(inventory_id, validated_data)
                logger.info(f"Jobs créés: {jobs_result['jobs_created']} job(s), {jobs_result['job_details_created']} job detail(s)")
                
                # 8. Identifier les emplacements non consommés (information uniquement, non bloquant)
                # Cette étape est informative et ne doit pas bloquer le traitement
                # Elle est exécutée après la transaction pour ne pas ralentir le traitement
                unconsumed_locations = self._get_unconsumed_locations(inventory_id, validated_data)
                logger.info(f"Emplacements non consommés identifiés: {len(unconsumed_locations)} emplacement(s)")
                
                return {
                    'success': True,
                    'message': f"Import réussi: {len(created_objects)} enregistrement(s) créé(s), {sync_result['updated_count']} emplacement(s) synchronisé(s), {jobs_result['jobs_created']} job(s) créé(s)",
                    'errors': [],
                    'imported_count': len(created_objects),
                    'locations_updated': sync_result['updated_count'],
                    'unconsumed_locations': unconsumed_locations,
                    'unconsumed_locations_count': len(unconsumed_locations),
                    'jobs_created': jobs_result['jobs_created'],
                    'job_details_created': jobs_result['job_details_created']
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de l'import: {str(e)}", exc_info=True)
            raise InventoryLocationJobValidationError(f"Erreur lors de l'import: {str(e)}")
    
    def _validate_excel_structure(self, df: pd.DataFrame) -> None:
        """
        Valide la structure du fichier Excel (colonnes requises)
        
        Args:
            df: DataFrame pandas
            
        Raises:
            InventoryLocationJobValidationError: Si la structure est invalide
        """
        required_columns = ['warehouse', 'emplacement', 'active', 'job', 'session_1', 'session_2']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise InventoryLocationJobValidationError(
                f"Colonnes manquantes dans le fichier Excel: {', '.join(missing_columns)}"
            )
    
    def _validate_row(
        self,
        row_dict: Dict[str, Any],
        row_number: int,
        inventory: Inventory
    ) -> List[Dict[str, Any]]:
        """
        Valide une ligne du fichier Excel
        
        Args:
            row_dict: Dictionnaire contenant les données de la ligne
            row_number: Numéro de la ligne (pour les messages d'erreur)
            inventory: Objet Inventory
            
        Returns:
            List[Dict]: Liste des erreurs de validation (vide si aucune erreur)
        """
        errors = []
        
        # 0. Déterminer si la ligne est active
        active_value = row_dict.get('active', '')
        # Normaliser la valeur active (gérer différents formats: False, false, 0, "False", etc.)
        is_active = self._normalize_boolean(active_value)
        
        # 1. Validation du warehouse
        warehouse_value = str(row_dict.get('warehouse', '')).strip()
        if not warehouse_value:
            errors.append({
                'row_number': row_number,
                'field': 'warehouse',
                'value': warehouse_value,
                'message': 'Le champ warehouse est obligatoire'
            })
        else:
            # Vérifier que le warehouse existe
            try:
                warehouse = self.warehouse_repo.get_by_reference(warehouse_value)
            except Exception:
                errors.append({
                    'row_number': row_number,
                    'field': 'warehouse',
                    'value': warehouse_value,
                    'message': f"Le warehouse '{warehouse_value}' n'existe pas"
                })
                return errors  # Pas besoin de continuer si le warehouse n'existe pas
            
            # Vérifier que le warehouse appartient à l'inventaire
            if not Setting.objects.filter(
                inventory=inventory,
                warehouse=warehouse
            ).exists():
                errors.append({
                    'row_number': row_number,
                    'field': 'warehouse',
                    'value': warehouse_value,
                    'message': f"Le warehouse '{warehouse_value}' n'appartient pas à l'inventaire '{inventory.label}'"
                })
                return errors  # Pas besoin de continuer si le warehouse n'appartient pas à l'inventaire
            
            # Stocker warehouse_id pour la création des jobs
            row_dict['warehouse_id'] = warehouse.id
        
        # 2. Validation de l'emplacement
        emplacement_value = str(row_dict.get('emplacement', '')).strip()
        if not emplacement_value:
            errors.append({
                'row_number': row_number,
                'field': 'emplacement',
                'value': emplacement_value,
                'message': 'Le champ emplacement est obligatoire'
            })
        else:
            # Vérifier que l'emplacement existe
            try:
                location = Location.objects.get(
                    location_reference=emplacement_value,
                    is_deleted=False
                )
                row_dict['emplacement_id'] = location.id
            except Location.DoesNotExist:
                errors.append({
                    'row_number': row_number,
                    'field': 'emplacement',
                    'value': emplacement_value,
                    'message': f"L'emplacement '{emplacement_value}' n'existe pas"
                })
                return errors  # Pas besoin de continuer si l'emplacement n'existe pas
            
            # Vérifier que l'emplacement est lié au warehouse
            # Les emplacements sont liés aux warehouses via: location -> sous_zone -> zone -> warehouse
            location_obj = Location.objects.select_related(
                'sous_zone__zone__warehouse'
            ).get(id=location.id)
            
            if location_obj.sous_zone.zone.warehouse.id != warehouse.id:
                errors.append({
                    'row_number': row_number,
                    'field': 'emplacement',
                    'value': emplacement_value,
                    'message': f"L'emplacement '{emplacement_value}' n'est pas lié au warehouse '{warehouse_value}'"
                })
        
        # 3. Validation du job (format job-XX) - Obligatoire seulement si active = true
        job_value = str(row_dict.get('job', '')).strip()
        if is_active:
            # Si active = true, job est obligatoire
            if not job_value:
                errors.append({
                    'row_number': row_number,
                    'field': 'job',
                    'value': job_value,
                    'message': 'Le champ job est obligatoire lorsque active est true'
                })
            else:
                # Vérifier le format job-XX
                job_pattern = r'^job-(\d+)$'
                match = re.match(job_pattern, job_value, re.IGNORECASE)
                if not match:
                    errors.append({
                        'row_number': row_number,
                        'field': 'job',
                        'value': job_value,
                        'message': f"Le format du job '{job_value}' est invalide. Format attendu: job-XX (ex: job-01, job-02)"
                    })
                else:
                    # Stocker le numéro du job pour la validation d'incrémentation
                    row_dict['job_number'] = int(match.group(1))
        else:
            # Si active = false, job n'est pas obligatoire mais on peut quand même le valider s'il est présent
            if job_value:
                job_pattern = r'^job-(\d+)$'
                match = re.match(job_pattern, job_value, re.IGNORECASE)
                if match:
                    # Stocker le numéro du job même si active = false (pour la validation d'incrémentation)
                    row_dict['job_number'] = int(match.group(1))
                else:
                    errors.append({
                        'row_number': row_number,
                        'field': 'job',
                        'value': job_value,
                        'message': f"Le format du job '{job_value}' est invalide. Format attendu: job-XX (ex: job-01, job-02)"
                    })
        
        # 4. Validation de session_1 (equipe-1000 à equipe-1999) - Obligatoire seulement si active = true
        session_1_value = str(row_dict.get('session_1', '')).strip() if pd.notna(row_dict.get('session_1')) else ''
        if is_active:
            # Si active = true, session_1 est obligatoire
            if not session_1_value:
                errors.append({
                    'row_number': row_number,
                    'field': 'session_1',
                    'value': session_1_value,
                    'message': 'Le champ session_1 est obligatoire lorsque active est true'
                })
            else:
                session_1_pattern = r'^equipe-(\d+)$'
                match = re.match(session_1_pattern, session_1_value, re.IGNORECASE)
                if not match:
                    errors.append({
                        'row_number': row_number,
                        'field': 'session_1',
                        'value': session_1_value,
                        'message': f"Le format de session_1 '{session_1_value}' est invalide. Format attendu: equipe-XXXX"
                    })
                else:
                    session_number = int(match.group(1))
                    if session_number < 1000 or session_number > 1999:
                        errors.append({
                            'row_number': row_number,
                            'field': 'session_1',
                            'value': session_1_value,
                            'message': f"La session_1 '{session_1_value}' est hors plage. Plage attendue: equipe-1000 à equipe-1999"
                        })
        else:
            # Si active = false, session_1 n'est pas obligatoire mais on peut quand même le valider s'il est présent
            if session_1_value:
                session_1_pattern = r'^equipe-(\d+)$'
                match = re.match(session_1_pattern, session_1_value, re.IGNORECASE)
                if not match:
                    errors.append({
                        'row_number': row_number,
                        'field': 'session_1',
                        'value': session_1_value,
                        'message': f"Le format de session_1 '{session_1_value}' est invalide. Format attendu: equipe-XXXX"
                    })
                else:
                    session_number = int(match.group(1))
                    if session_number < 1000 or session_number > 1999:
                        errors.append({
                            'row_number': row_number,
                            'field': 'session_1',
                            'value': session_1_value,
                            'message': f"La session_1 '{session_1_value}' est hors plage. Plage attendue: equipe-1000 à equipe-1999"
                        })
        
        # 5. Validation de session_2 (equipe-2000 à equipe-2999) - Obligatoire seulement si active = true
        session_2_value = str(row_dict.get('session_2', '')).strip() if pd.notna(row_dict.get('session_2')) else ''
        if is_active:
            # Si active = true, session_2 est obligatoire
            if not session_2_value:
                errors.append({
                    'row_number': row_number,
                    'field': 'session_2',
                    'value': session_2_value,
                    'message': 'Le champ session_2 est obligatoire lorsque active est true'
                })
            else:
                session_2_pattern = r'^equipe-(\d+)$'
                match = re.match(session_2_pattern, session_2_value, re.IGNORECASE)
                if not match:
                    errors.append({
                        'row_number': row_number,
                        'field': 'session_2',
                        'value': session_2_value,
                        'message': f"Le format de session_2 '{session_2_value}' est invalide. Format attendu: equipe-XXXX"
                    })
                else:
                    session_number = int(match.group(1))
                    if session_number < 2000 or session_number > 2999:
                        errors.append({
                            'row_number': row_number,
                            'field': 'session_2',
                            'value': session_2_value,
                            'message': f"La session_2 '{session_2_value}' est hors plage. Plage attendue: equipe-2000 à equipe-2999"
                        })
        else:
            # Si active = false, session_2 n'est pas obligatoire mais on peut quand même le valider s'il est présent
            if session_2_value:
                session_2_pattern = r'^equipe-(\d+)$'
                match = re.match(session_2_pattern, session_2_value, re.IGNORECASE)
                if not match:
                    errors.append({
                        'row_number': row_number,
                        'field': 'session_2',
                        'value': session_2_value,
                        'message': f"Le format de session_2 '{session_2_value}' est invalide. Format attendu: equipe-XXXX"
                    })
                else:
                    session_number = int(match.group(1))
                    if session_number < 2000 or session_number > 2999:
                        errors.append({
                            'row_number': row_number,
                            'field': 'session_2',
                            'value': session_2_value,
                            'message': f"La session_2 '{session_2_value}' est hors plage. Plage attendue: equipe-2000 à equipe-2999"
                        })
        
        # Stocker is_active dans row_dict pour utilisation ultérieure
        row_dict['is_active'] = is_active
        
        return errors
    
    def _normalize_boolean(self, value) -> bool:
        """
        Normalise une valeur en booléen
        
        Args:
            value: Valeur à normaliser
            
        Returns:
            bool: True ou False
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value = value.strip().lower()
            if value in ('', 'none', 'null', 'n/a', 'na', 'false', '0', 'no', 'non', 'n', 'f', 'non actif', 'inactif'):
                return False
            if value in ('true', '1', 'yes', 'oui', 'o', 'y', 't', 'actif', 'active'):
                return True
        if isinstance(value, (int, float)):
            return bool(value)
        return False
    
    def _validate_job_increment(self, validated_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Valide que les jobs sont incrémentés sans rupture
        Ne valide que les lignes où active = true
        
        Args:
            validated_data: Liste des données validées (contient 'job_number' et 'is_active')
            
        Returns:
            List[Dict]: Liste des erreurs (vide si aucune erreur)
        """
        errors = []
        
        # Extraire les numéros de jobs uniquement pour les lignes actives et les trier
        job_numbers = sorted([
            data['job_number'] 
            for data in validated_data 
            if data.get('is_active', False) and 'job_number' in data and data['job_number'] is not None
        ])
        
        if not job_numbers:
            return errors
        
        # Vérifier l'incrémentation (doit commencer à 1 et être continue)
        if job_numbers[0] != 1:
            errors.append({
                'row_number': None,  # Erreur globale
                'field': 'job',
                'value': f'job-{job_numbers[0]:02d}',
                'message': f"Les jobs doivent commencer à job-01. Premier job trouvé: job-{job_numbers[0]:02d}"
            })
            return errors
        
        # Vérifier qu'il n'y a pas de rupture dans l'incrémentation
        expected_number = 1
        for job_number in job_numbers:
            if job_number != expected_number:
                errors.append({
                    'row_number': None,  # Erreur globale
                    'field': 'job',
                    'value': f'job-{job_number:02d}',
                    'message': f"Rupture d'incrémentation détectée. Job attendu: job-{expected_number:02d}, Job trouvé: job-{job_number:02d}. Jobs manquants: {', '.join([f'job-{i:02d}' for i in range(expected_number, job_number)])}"
                })
                break
            expected_number += 1
        
        return errors
    
    def _sync_location_active_status(self, validated_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synchronise le champ active du fichier Excel avec Location.is_active
        
        Cette méthode ne s'exécute que si toutes les validations sont réussies.
        Elle met à jour uniquement les emplacements présents dans le fichier Excel.
        
        Règles de mise à jour :
        - Excel false + Location true → mettre is_active = false
        - Excel true + Location false → mettre is_active = true
        - Excel true + Location true → aucune action
        - Excel false + Location false → aucune action
        
        Args:
            validated_data: Liste des données validées (contient 'emplacement_id' et 'active_excel')
            
        Returns:
            Dict contenant le nombre d'emplacements mis à jour
        """
        updated_count = 0
        
        # Grouper par emplacement_id pour éviter les doublons
        location_updates = {}
        for data in validated_data:
            emplacement_id = data.get('emplacement_id')
            active_excel = data.get('active_excel', False)
            
            if emplacement_id:
                # Si l'emplacement apparaît plusieurs fois, prendre la dernière valeur
                location_updates[emplacement_id] = active_excel
        
        if not location_updates:
            logger.info("Aucun emplacement à synchroniser")
            return {'updated_count': 0}
        
        # Récupérer tous les emplacements concernés en une seule requête
        location_ids = list(location_updates.keys())
        locations = Location.objects.filter(id__in=location_ids)
        
        # Mettre à jour les emplacements selon les règles
        locations_to_update = []
        for location in locations:
            active_excel = location_updates[location.id]
            current_is_active = location.is_active
            
            # Appliquer les règles de mise à jour
            if active_excel is False and current_is_active is True:
                # Excel false + Location true → mettre is_active = false
                location.is_active = False
                locations_to_update.append(location)
                logger.debug(f"Emplacement {location.id} ({location.location_reference}): is_active changé de True à False")
            elif active_excel is True and current_is_active is False:
                # Excel true + Location false → mettre is_active = true
                location.is_active = True
                locations_to_update.append(location)
                logger.debug(f"Emplacement {location.id} ({location.location_reference}): is_active changé de False à True")
            # Les autres cas (true+true, false+false) ne nécessitent aucune action
        
        # Mettre à jour en masse si nécessaire
        if locations_to_update:
            Location.objects.bulk_update(locations_to_update, ['is_active'])
            updated_count = len(locations_to_update)
            logger.info(f"Synchronisation terminée: {updated_count} emplacement(s) mis à jour")
        else:
            logger.info("Aucun emplacement nécessitant une mise à jour")
        
        return {
            'updated_count': updated_count
        }
    
    def _get_unconsumed_locations(
        self,
        inventory_id: int,
        validated_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identifie les emplacements non consommés (liés au warehouse de l'inventaire mais absents du fichier Excel)
        
        Cette méthode est informative uniquement et ne doit pas bloquer le traitement.
        Elle ne modifie aucune donnée en base.
        
        Args:
            inventory_id: ID de l'inventaire
            validated_data: Liste des données validées du fichier Excel (contient 'emplacement_id')
            
        Returns:
            List[Dict]: Liste des emplacements non consommés avec leurs informations
        """
        try:
            # Récupérer tous les warehouses associés à cet inventaire
            warehouses = self.inventory_repo.get_warehouses_by_inventory_id(inventory_id)
            
            if not warehouses:
                logger.info("Aucun warehouse associé à l'inventaire, aucun emplacement non consommé à identifier")
                return []
            
            # Récupérer tous les emplacements présents dans le fichier Excel
            excel_location_ids = set([
                data.get('emplacement_id')
                for data in validated_data
                if data.get('emplacement_id')
            ])
            
            # Pour chaque warehouse, récupérer tous les emplacements liés
            all_warehouse_location_ids = set()
            for warehouse in warehouses:
                # Récupérer tous les emplacements du warehouse via: location -> sous_zone -> zone -> warehouse
                warehouse_locations = Location.objects.filter(
                    sous_zone__zone__warehouse=warehouse,
                    is_deleted=False
                ).values_list('id', flat=True)
                
                all_warehouse_location_ids.update(warehouse_locations)
            
            # Identifier les emplacements absents du fichier Excel
            unconsumed_location_ids = all_warehouse_location_ids - excel_location_ids
            
            if not unconsumed_location_ids:
                logger.info("Tous les emplacements du warehouse sont présents dans le fichier Excel")
                return []
            
            # Récupérer les informations des emplacements non consommés
            unconsumed_locations = Location.objects.filter(
                id__in=unconsumed_location_ids
            ).select_related(
                'sous_zone__zone__warehouse'
            ).values(
                'id',
                'location_reference',
                'reference',
                'sous_zone__zone__warehouse__warehouse_name',
                'sous_zone__zone__warehouse__reference',
                'is_active'
            )
            
            # Formater les résultats
            result = [
                {
                    'id': loc['id'],
                    'location_reference': loc['location_reference'],
                    'reference': loc['reference'],
                    'warehouse_name': loc['sous_zone__zone__warehouse__warehouse_name'],
                    'warehouse_reference': loc['sous_zone__zone__warehouse__reference'],
                    'is_active': loc['is_active']
                }
                for loc in unconsumed_locations
            ]
            
            logger.info(f"Emplacements non consommés identifiés: {len(result)} emplacement(s)")
            return result
            
        except Exception as e:
            # En cas d'erreur, ne pas bloquer le traitement, juste logger l'erreur
            logger.warning(f"Erreur lors de l'identification des emplacements non consommés: {str(e)}")
            return []  # Retourner une liste vide pour ne pas bloquer le traitement
    
    def _create_jobs_and_details(
        self,
        inventory_id: int,
        validated_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Crée automatiquement les Jobs et JobDetails à partir des données importées
        
        Cette méthode applique exactement la même logique métier que JobCreateAPIView.
        Elle regroupe les lignes par job, trie par ordre croissant, et crée les Jobs/JobDetails.
        
        Args:
            inventory_id: ID de l'inventaire
            validated_data: Liste des données validées (contient warehouse_id, job, emplacement_id)
            
        Returns:
            Dict contenant le nombre de jobs et job details créés
        """
        try:
            # Récupérer l'inventaire
            inventory = self.inventory_repo.get_by_id(inventory_id)
            
            # Vérifier qu'il y a au moins deux comptages pour cet inventaire
            countings = Counting.objects.filter(inventory=inventory).order_by('order')
            if countings.count() < 2:
                logger.warning(f"Il faut au moins deux comptages pour créer les jobs. Comptages trouvés: {countings.count()}")
                return {'jobs_created': 0, 'job_details_created': 0}
            
            counting1 = countings.filter(order=1).first()  # 1er comptage
            counting2 = countings.filter(order=2).first()  # 2ème comptage
            
            if not counting1 or not counting2:
                logger.warning(f"Comptages d'ordre 1 et 2 requis. Comptages trouvés: {countings.count()}")
                return {'jobs_created': 0, 'job_details_created': 0}
            
            # Filtrer uniquement les lignes avec job (ignorer les lignes où active = false et job est vide)
            data_with_jobs = [
                data for data in validated_data
                if data.get('job') and data.get('warehouse_id') and data.get('emplacement_id')
            ]
            
            if not data_with_jobs:
                logger.info("Aucune ligne avec job à traiter")
                return {'jobs_created': 0, 'job_details_created': 0}
            
            # Regrouper par warehouse et job
            jobs_by_warehouse = {}
            for data in data_with_jobs:
                warehouse_id = data['warehouse_id']
                job_reference = data['job']
                emplacement_id = data['emplacement_id']
                
                key = (warehouse_id, job_reference)
                if key not in jobs_by_warehouse:
                    jobs_by_warehouse[key] = []
                jobs_by_warehouse[key].append(emplacement_id)
            
            # Trier les jobs par ordre croissant (extraire le numéro du job)
            def get_job_number(job_ref):
                """Extrait le numéro du job (ex: job-01 -> 1)"""
                import re
                match = re.match(r'^job-(\d+)$', job_ref, re.IGNORECASE)
                return int(match.group(1)) if match else 0
            
            sorted_jobs = sorted(jobs_by_warehouse.keys(), key=lambda x: get_job_number(x[1]))
            
            jobs_created = 0
            job_details_created = 0
            
            # Créer les Jobs et JobDetails pour chaque combinaison warehouse/job
            for warehouse_id, job_reference in sorted_jobs:
                try:
                    # Récupérer le warehouse
                    warehouse = Warehouse.objects.get(id=warehouse_id)
                    
                    # Vérifier si le job existe déjà pour cet inventaire avec cette référence
                    existing_job = Job.objects.filter(
                        inventory=inventory,
                        warehouse=warehouse,
                        reference=job_reference
                    ).first()
                    
                    if existing_job:
                        logger.info(f"Job {job_reference} existe déjà pour l'inventaire {inventory.reference} et le warehouse {warehouse.warehouse_name}")
                        # Récupérer les emplacements pour ce job existant
                        emplacement_ids = jobs_by_warehouse[(warehouse_id, job_reference)]
                        
                        # Vérifier quels emplacements ne sont pas déjà dans ce job
                        existing_location_ids = set(
                            JobDetail.objects.filter(
                                job=existing_job
                            ).values_list('location_id', flat=True)
                        )
                        
                        new_location_ids = [
                            loc_id for loc_id in emplacement_ids
                            if loc_id not in existing_location_ids
                        ]
                        
                        if new_location_ids:
                            # Créer les JobDetails pour les nouveaux emplacements
                            locations = Location.objects.filter(id__in=new_location_ids)
                            # Trier les emplacements par location_reference (ordre croissant)
                            locations = sorted(locations, key=lambda l: l.location_reference)
                            
                            details_count = self._create_job_details_for_job(
                                existing_job, locations, counting1, counting2
                            )
                            job_details_created += details_count
                            logger.info(f"Ajouté {details_count} job detail(s) au job existant {job_reference}")
                        continue
                    
                    # Récupérer les emplacements pour ce job
                    emplacement_ids = jobs_by_warehouse[(warehouse_id, job_reference)]
                    locations = Location.objects.filter(id__in=emplacement_ids)
                    
                    # Trier les emplacements par location_reference (ordre croissant)
                    locations = sorted(locations, key=lambda l: l.location_reference)
                    
                    # Vérifier que tous les emplacements appartiennent au warehouse
                    invalid_locations = [
                        loc for loc in locations
                        if loc.sous_zone.zone.warehouse.id != warehouse_id
                    ]
                    if invalid_locations:
                        logger.warning(f"Certains emplacements n'appartiennent pas au warehouse {warehouse.warehouse_name}")
                        continue
                    
                    # Vérifier qu'aucun emplacement n'est déjà affecté à un autre job pour cet inventaire
                    existing_job_details = JobDetail.objects.filter(
                        location_id__in=emplacement_ids,
                        job__inventory=inventory
                    ).exclude(job__reference=job_reference)
                    
                    if existing_job_details.exists():
                        conflicting_locations = [
                            jd.location.location_reference
                            for jd in existing_job_details.select_related('location', 'job')
                        ]
                        logger.warning(f"Certains emplacements sont déjà affectés à d'autres jobs: {', '.join(conflicting_locations)}")
                        continue
                    
                    # Créer le Job avec la référence du fichier Excel
                    job = Job.objects.create(
                        reference=job_reference,  # Utiliser la référence du fichier Excel (ex: job-01)
                        status='EN ATTENTE',
                        en_attente_date=timezone.now(),
                        warehouse=warehouse,
                        inventory=inventory
                    )
                    jobs_created += 1
                    logger.info(f"Job {job.reference} créé pour l'inventaire {inventory.reference} et le warehouse {warehouse.warehouse_name}")
                    
                    # Créer les JobDetails selon la logique des comptages
                    details_count = self._create_job_details_for_job(
                        job, locations, counting1, counting2
                    )
                    job_details_created += details_count
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la création du job {job_reference}: {str(e)}", exc_info=True)
                    # Continuer avec le job suivant même en cas d'erreur
                    continue
            
            return {
                'jobs_created': jobs_created,
                'job_details_created': job_details_created
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des jobs et job details: {str(e)}", exc_info=True)
            # Ne pas bloquer le traitement, retourner 0
            return {'jobs_created': 0, 'job_details_created': 0}
    
    def _create_job_details_for_job(
        self,
        job: Job,
        locations: List[Location],
        counting1: Counting,
        counting2: Counting
    ) -> int:
        """
        Crée les JobDetails pour un job selon la logique des comptages
        
        Args:
            job: Le job pour lequel créer les JobDetails
            locations: Liste des emplacements (déjà triés)
            counting1: Premier comptage
            counting2: Deuxième comptage
            
        Returns:
            int: Nombre de JobDetails créés
        """
        details_count = 0
        
        if counting1.count_mode == "image de stock":
            # Cas 1: 1er comptage = image de stock
            # Créer les emplacements seulement pour le 2ème comptage
            logger.debug(f"Configuration 'image de stock' détectée pour le job {job.reference}")
            
            for location in locations:
                JobDetail.objects.create(
                    reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                    location=location,
                    job=job,
                    counting=counting2,  # Assigner au 2ème comptage
                    status='EN ATTENTE',
                    en_attente_date=timezone.now()
                )
                details_count += 1
        else:
            # Cas 2: 1er comptage différent de "image de stock"
            # Dupliquer les emplacements pour les deux comptages
            logger.debug(f"Configuration normale détectée pour le job {job.reference}")
            
            for location in locations:
                # Créer un JobDetail pour le 1er comptage
                JobDetail.objects.create(
                    reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                    location=location,
                    job=job,
                    counting=counting1,
                    status='EN ATTENTE',
                    en_attente_date=timezone.now()
                )
                details_count += 1
                
                # Créer un JobDetail pour le 2ème comptage
                JobDetail.objects.create(
                    reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                    location=location,
                    job=job,
                    counting=counting2,
                    status='EN ATTENTE',
                    en_attente_date=timezone.now()
                )
                details_count += 1
        
        return details_count

