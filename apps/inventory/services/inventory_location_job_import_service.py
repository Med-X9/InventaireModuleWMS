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
from apps.masterdata.models import Warehouse, Location, InventoryLocationJob, ImportTask, ImportError
from apps.inventory.repositories.inventory_location_job_repository import InventoryLocationJobRepository
from apps.masterdata.repositories.warehouse_repository import WarehouseRepository
from apps.masterdata.repositories.location_repository import LocationRepository
from apps.masterdata.exceptions import InventoryLocationJobValidationError
from apps.inventory.repositories.inventory_repository import InventoryRepository

logger = logging.getLogger(__name__)

# Taille des chunks pour le tracking
CHUNK_SIZE = 1000  # Nombre de lignes par chunk


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
        user_id: Optional[int] = None,
        callback: Optional[callable] = None
    ) -> ImportTask:
        """
        Lance l'import de manière asynchrone dans un thread séparé
        
        Args:
            inventory_id: ID de l'inventaire
            file_path: Chemin vers le fichier Excel
            user_id: ID de l'utilisateur (optionnel, pour créer ImportTask)
            callback: Fonction de callback appelée avec le résultat (optionnel)
            
        Returns:
            ImportTask: La tâche d'import créée
        """
        import os
        from apps.users.models import UserApp
        
        # Créer une ImportTask pour suivre le traitement
        file_name = os.path.basename(file_path)
        import_task = ImportTask.objects.create(
            user_id=user_id or 1,  # Utiliser l'utilisateur par défaut si non fourni
            inventory_id=inventory_id,
            file_path=file_path,
            file_name=file_name,
            status='PENDING',
            total_rows=0
        )
        
        def import_task_thread():
            from django.db import connections
            import_task_id = import_task.id  # Capturer l'ID avant le thread
            try:
                # Log immédiat pour confirmer que le thread démarre
                print(f"[THREAD] Thread d'import démarré pour ImportTask {import_task_id}")
                logger.info(f"Thread d'import démarré pour ImportTask {import_task_id}")
                
                # Récupérer l'objet ImportTask dans le thread (important pour les threads)
                task = ImportTask.objects.get(id=import_task_id)
                print(f"[THREAD] ImportTask {import_task_id} récupéré, statut actuel: {task.status}")
                
                task.status = 'VALIDATING'
                task.save()
                print(f"[THREAD] Statut mis à VALIDATING pour ImportTask {import_task_id}")
                logger.info(f"Début de l'import pour ImportTask {import_task_id}")
                
                print(f"[THREAD] Appel de import_from_excel pour ImportTask {import_task_id}")
                result = self.import_from_excel(inventory_id, file_path, task)
                print(f"[THREAD] import_from_excel terminé pour ImportTask {import_task_id}, success={result.get('success') if isinstance(result, dict) else 'N/A'}")
                
                # Recharger l'objet task depuis la base de données
                task.refresh_from_db()
                
                # Vérifier que le résultat est valide
                if not isinstance(result, dict) or 'success' not in result:
                    logger.error(f"Résultat invalide de import_from_excel pour ImportTask {task.id}: {result}")
                    result = {
                        'success': False,
                        'message': 'Erreur: résultat invalide de l\'import',
                        'errors': []
                    }
                
                logger.info(f"Résultat de l'import pour ImportTask {task.id}: success={result.get('success')}, errors={len(result.get('errors', []))}")
                
                # Mettre à jour l'ImportTask avec les résultats
                if result.get('success', False):
                    task.status = 'COMPLETED'
                    task.imported_count = result.get('imported_count', 0)
                    task.updated_count = result.get('imported_updated', 0)
                    task.validated_rows = result.get('imported_count', 0)
                    task.processed_rows = result.get('imported_count', 0)
                    task.error_count = 0
                    task.error_message = None
                else:
                    task.status = 'CANCELLED'
                    errors_list = result.get('errors', [])
                    task.error_count = len(errors_list)
                    task.error_message = result.get('message', 'Erreurs détectées')
                    
                    # Stocker les erreurs dans ImportError
                    logger.info(f"Enregistrement de {len(errors_list)} erreur(s) dans ImportError")
                    for error in errors_list:
                        # S'assurer que row_number n'est jamais None (0 pour les erreurs globales)
                        row_number = error.get('row_number')
                        if row_number is None:
                            row_number = 0
                        
                        try:
                            ImportError.objects.create(
                                import_task=task,
                                row_number=row_number,
                                error_type=error.get('field', 'validation'),
                                error_message=error.get('message', 'Erreur inconnue'),
                                field_name=error.get('field'),
                                field_value=str(error.get('value', '')),
                                row_data=error
                            )
                        except Exception as e:
                            logger.error(f"Erreur lors de l'enregistrement d'une erreur d'import: {str(e)}", exc_info=True)
                
                task.save()
                logger.info(f"ImportTask {task.id} mis à jour: status={task.status}, errors={task.error_count}")
                
                if callback:
                    callback(result)
                
                # Fermer les connexions à la base de données
                connections.close_all()
                logger.info(f"Thread d'import terminé pour ImportTask {task.id}")
                    
            except InventoryLocationJobValidationError as e:
                # Capturer spécifiquement les erreurs de validation
                logger.error(f"Erreur de validation lors de l'import asynchrone: {str(e)}", exc_info=True)
                try:
                    task = ImportTask.objects.get(id=import_task_id)
                    task.status = 'CANCELLED'
                    task.error_message = f"Erreur de validation: {str(e)}"
                    task.error_count = 1
                    
                    # Enregistrer l'erreur dans ImportError
                    try:
                        ImportError.objects.create(
                            import_task=task,
                            row_number=0,
                            error_type='validation',
                            error_message=str(e),
                            field_name=None,
                            field_value='',
                            row_data={'exception': str(e)}
                        )
                    except Exception as err:
                        logger.error(f"Erreur lors de l'enregistrement de l'erreur de validation: {str(err)}", exc_info=True)
                    
                    task.save()
                except Exception as db_err:
                    logger.error(f"Erreur lors de la mise à jour de ImportTask: {str(db_err)}", exc_info=True)
                
                if callback:
                    callback({
                        'success': False,
                        'message': f"Erreur de validation: {str(e)}",
                        'errors': [{
                            'row_number': 0,
                            'field': 'validation',
                            'value': '',
                            'message': str(e)
                        }]
                    })
                
                # Fermer les connexions à la base de données
                connections.close_all()
                logger.info(f"Thread d'import terminé avec erreur de validation pour ImportTask {import_task_id}")
            except Exception as e:
                logger.error(f"Erreur lors de l'import asynchrone: {str(e)}", exc_info=True)
                import traceback
                traceback_str = traceback.format_exc()
                logger.error(f"Traceback complet: {traceback_str}")
                
                try:
                    task = ImportTask.objects.get(id=import_task_id)
                    task.status = 'FAILED'
                    task.error_message = f"Erreur lors de l'import: {str(e)}"
                    task.error_count = 1
                    
                    # Enregistrer l'erreur dans ImportError
                    try:
                        ImportError.objects.create(
                            import_task=task,
                            row_number=0,
                            error_type='system',
                            error_message=str(e),
                            field_name=None,
                            field_value='',
                            row_data={'exception': str(e), 'traceback': traceback_str}
                        )
                    except Exception as err:
                        logger.error(f"Erreur lors de l'enregistrement de l'erreur système: {str(err)}", exc_info=True)
                    
                    task.save()
                except Exception as db_err:
                    logger.error(f"Erreur lors de la mise à jour de ImportTask: {str(db_err)}", exc_info=True)
                
                if callback:
                    callback({
                        'success': False,
                        'message': f"Erreur lors de l'import: {str(e)}",
                        'errors': [{
                            'row_number': 0,
                            'field': 'system',
                            'value': '',
                            'message': str(e)
                        }]
                    })
                
                # Fermer les connexions à la base de données
                connections.close_all()
                logger.error(f"Thread d'import terminé avec erreur système pour ImportTask {import_task_id}: {str(e)}")
        
        # Utiliser daemon=False pour que le thread continue même si le processus principal se termine
        # Mais attention : cela peut empêcher le serveur de s'arrêter proprement
        thread = threading.Thread(target=import_task_thread, daemon=False)
        print(f"[MAIN] Lancement du thread d'import pour l'inventaire {inventory_id}, ImportTask ID: {import_task.id}")
        logger.info(f"Lancement du thread d'import pour l'inventaire {inventory_id}, ImportTask ID: {import_task.id}")
        thread.start()
        print(f"[MAIN] Thread d'import démarré avec succès pour ImportTask ID: {import_task.id}")
        logger.info(f"Thread d'import démarré avec succès pour ImportTask ID: {import_task.id}")
        
        return import_task
    
    def import_from_excel(self, inventory_id: int, file_path: str, import_task: Optional[ImportTask] = None) -> Dict[str, Any]:
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
            print(f"[IMPORT] Lecture du fichier Excel: {file_path}")
            logger.info(f"Lecture du fichier Excel: {file_path}")
            df = pd.read_excel(file_path, engine='openpyxl')
            print(f"[IMPORT] Fichier Excel lu: {len(df)} lignes")
            
            # Mettre à jour le nombre total de lignes dans ImportTask
            if import_task:
                import_task.total_rows = len(df)
                import_task.status = 'PROCESSING'
                import_task.save()
                print(f"[IMPORT] Statut mis à PROCESSING, {len(df)} lignes à traiter")
            
            # Normaliser les noms de colonnes (minuscules, sans espaces)
            df.columns = df.columns.str.strip().str.lower()
            print(f"[IMPORT] Colonnes normalisées: {list(df.columns)}")
            
            # Valider la structure du fichier
            try:
                print(f"[IMPORT] Validation de la structure du fichier...")
                self._validate_excel_structure(df)
                print(f"[IMPORT] Structure validée avec succès")
            except InventoryLocationJobValidationError as e:
                # Convertir l'exception en erreur de validation
                logger.warning(f"Erreur de structure du fichier: {str(e)}")
                return {
                    'success': False,
                    'message': str(e),
                    'errors': [{
                        'row_number': 0,
                        'field': 'structure',
                        'value': '',
                        'message': str(e)
                    }],
                    'imported_count': 0
                }
            
            # Valider toutes les lignes AVANT toute insertion
            print(f"[IMPORT] Début de la validation des {len(df)} lignes...")
            validation_errors = []
            validated_data = []
            
            for index, row in df.iterrows():
                # Log de progression tous les 1000 lignes
                if (index + 1) % 1000 == 0:
                    print(f"[IMPORT] Validation en cours: {index + 1}/{len(df)} lignes traitées...")
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
                    job_value_raw = row_dict.get('job', '')
                    # Normaliser les valeurs NaN/pandas en chaîne vide
                    if pd.isna(job_value_raw) or str(job_value_raw).lower() in ('nan', 'none', 'null', ''):
                        job_value = ''
                    else:
                        job_value = str(job_value_raw).strip()
                    
                    job_number = None
                    if job_value:
                        job_pattern = r'^JOB-(\d{4})$'
                        match = re.match(job_pattern, job_value)
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
                        'session_1': self._normalize_excel_value(row_dict.get('session_1')),
                        'session_2': self._normalize_excel_value(row_dict.get('session_2')),
                        'row_number': row_number,  # Pour les messages d'erreur de validation globale
                    })
            
            print(f"[IMPORT] Validation terminée: {len(validation_errors)} erreur(s), {len(validated_data)} ligne(s) valide(s)")
            
            # Si des erreurs de validation, ne rien insérer
            if validation_errors:
                print(f"[IMPORT] Import annulé: {len(validation_errors)} erreur(s) détectée(s)")
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
            
            # Valider la cohérence des sessions par job
            session_errors = self._validate_job_sessions_consistency(validated_data)
            if session_errors:
                logger.warning(f"Import annulé: erreur(s) de cohérence des sessions par job")
                return {
                    'success': False,
                    'message': f"Import annulé: erreur(s) de cohérence des sessions par job",
                    'errors': session_errors,
                    'imported_count': 0
                }
            
            # Valider qu'un job est affecté à une seule équipe dans les deux sessions
            single_team_errors = self._validate_job_single_team_in_sessions(validated_data)
            if single_team_errors:
                logger.warning(f"Import annulé: erreur(s) de validation - un job doit être affecté à une seule équipe dans les deux sessions")
                return {
                    'success': False,
                    'message': f"Import annulé: erreur(s) de validation - un job doit être affecté à une seule équipe dans les deux sessions",
                    'errors': single_team_errors,
                    'imported_count': 0
                }
            
            # Initialiser le tracking des chunks si import_task est fourni
            total_rows = len(validated_data)
            total_chunks = (total_rows + CHUNK_SIZE - 1) // CHUNK_SIZE if total_rows > 0 else 0
            
            if import_task and total_chunks > 0:
                chunks_progress = [
                    {
                        'chunk_number': i + 1,
                        'status': 'PENDING',
                        'start_row': (i * CHUNK_SIZE) + 1,
                        'end_row': min((i + 1) * CHUNK_SIZE, total_rows),
                        'processed_rows': 0,
                        'imported_count': 0,
                        'updated_count': 0,
                        'error_count': 0,
                        'started_at': None,
                        'completed_at': None,
                        'error_message': None
                    }
                    for i in range(total_chunks)
                ]
                import_task.set_chunks_progress(chunks_progress)
                logger.info(f"Tracking des chunks initialisé: {total_chunks} chunk(s) pour {total_rows} ligne(s)")
            
            # Si toutes les validations passent, procéder à la synchronisation puis à l'insertion
            with transaction.atomic():
                # 5bis. D'abord, purger toutes les données liées aux jobs de cet inventaire
                # (InventoryLocationJob, JobDetail, Job) pour repartir sur une base propre
                clear_stats = self._clear_inventory_jobs(inventory_id)
                logger.info(
                    f"Nettoyage initial de l'inventaire {inventory_id}: "
                    f"{clear_stats['deleted_job_details']} JobDetail supprimé(s), "
                    f"{clear_stats['deleted_location_jobs']} InventoryLocationJob supprimé(s), "
                    f"{clear_stats['deleted_jobs']} job(s) supprimé(s)"
                )

                # 6. Ensuite, synchroniser le champ active du fichier Excel avec Location.is_active
                # Cette étape s'exécute AVANT l'insertion dans InventoryLocationJob
                # Le champ active du fichier Excel sert uniquement à la synchronisation, pas à l'insertion
                sync_result = self._sync_location_active_status(validated_data)
                logger.info(f"Synchronisation des emplacements: {sync_result['updated_count']} emplacement(s) mis à jour")
                
                # 7. Traiter les données par chunks pour le tracking
                if import_task and total_chunks > 0:
                    # Traiter chaque chunk
                    for chunk_idx in range(total_chunks):
                        start_idx = chunk_idx * CHUNK_SIZE
                        end_idx = min(start_idx + CHUNK_SIZE, total_rows)
                        chunk_data = validated_data[start_idx:end_idx]
                        chunk_number = chunk_idx + 1
                        
                        # Mettre à jour le statut du chunk
                        import_task.update_chunk_progress(
                            chunk_number,
                            status='PROCESSING',
                            started_at=timezone.now().isoformat()
                        )
                        logger.info(f"Traitement du chunk {chunk_number}/{total_chunks} (lignes {start_idx + 1} à {end_idx})")
                        
                        try:
                            # Préparer les données du chunk pour l'upsert
                            chunk_data_to_upsert = [
                                {
                                    'inventaire_id': data['inventaire_id'],
                                    'emplacement_id': data['emplacement_id'],
                                    'job': data['job'],
                                    'session_1': data['session_1'],
                                    'session_2': data['session_2'],
                                }
                                for data in chunk_data
                            ]
                            
                            # Effectuer l'upsert pour ce chunk
                            chunk_upsert_result = self.repository.bulk_upsert(chunk_data_to_upsert, inventory_id)
                            
                            # Mettre à jour le tracking du chunk
                            import_task.update_chunk_progress(
                                chunk_number,
                                status='COMPLETED',
                                processed_rows=len(chunk_data),
                                imported_count=chunk_upsert_result.get('created', 0),
                                updated_count=chunk_upsert_result.get('updated', 0),
                                error_count=0,
                                completed_at=timezone.now().isoformat()
                            )
                            
                            logger.info(
                                f"Chunk {chunk_number}/{total_chunks} terminé: "
                                f"{chunk_upsert_result.get('created', 0)} créé(s), "
                                f"{chunk_upsert_result.get('updated', 0)} mis à jour"
                            )
                            
                        except Exception as e:
                            # En cas d'erreur sur un chunk, marquer comme FAILED
                            import_task.update_chunk_progress(
                                chunk_number,
                                status='FAILED',
                                error_message=str(e),
                                completed_at=timezone.now().isoformat()
                            )
                            logger.error(f"Erreur lors du traitement du chunk {chunk_number}: {str(e)}")
                            raise
                    
                    # Récupérer les résultats totaux depuis les chunks
                    chunks_progress = import_task.get_chunks_progress()
                    total_imported = sum(chunk.get('imported_count', 0) for chunk in chunks_progress)
                    total_updated = sum(chunk.get('updated_count', 0) for chunk in chunks_progress)
                    upsert_result = {
                        'created': total_imported,
                        'updated': total_updated
                    }
                else:
                    # Traitement normal sans chunks (pour compatibilité)
                    data_to_upsert = [
                        {
                            'inventaire_id': data['inventaire_id'],
                            'emplacement_id': data['emplacement_id'],
                            'job': data['job'],
                            'session_1': data['session_1'],
                            'session_2': data['session_2'],
                        }
                        for data in validated_data
                    ]
                    
                    # Effectuer l'upsert (update or insert) en masse
                    upsert_result = self.repository.bulk_upsert(data_to_upsert, inventory_id)
                
                logger.info(f"Import réussi: {upsert_result['created']} enregistrement(s) créé(s), {upsert_result['updated']} enregistrement(s) mis à jour dans InventoryLocationJob")
                
                # 9. Créer automatiquement les Jobs et JobDetails à partir des données importées
                # Cette étape s'exécute uniquement si toutes les étapes précédentes sont réussies
                # Elle est dans la transaction atomique pour garantir la cohérence
                jobs_result = self._create_jobs_and_details(inventory_id, validated_data)
                logger.info(f"Jobs créés: {jobs_result['jobs_created']} job(s), {jobs_result['job_details_created']} job detail(s)")
                
                # 8. Identifier les emplacements non consommés (présents en base mais absents du fichier Excel)
                unconsumed_locations = self._get_unconsumed_locations(inventory_id, validated_data)
                logger.info(f"Emplacements non consommés identifiés: {len(unconsumed_locations)} emplacement(s)")
                
                # 9. Supprimer/Nettoyer les données associées à ces emplacements non consommés
                # (JobDetail + liens InventoryLocationJob, et éventuellement jobs devenus vides)
                cleanup_stats = self._delete_unconsumed_locations(inventory_id, unconsumed_locations)
                logger.info(
                    "Nettoyage des emplacements non consommés: "
                    f"{cleanup_stats['deleted_job_details']} JobDetail supprimé(s), "
                    f"{cleanup_stats['deleted_location_jobs']} InventoryLocationJob supprimé(s), "
                    f"{cleanup_stats['deleted_jobs']} job(s) supprimé(s)"
                )
                
                return {
                    'success': True,
                    'message': f"Import réussi: {upsert_result['created']} enregistrement(s) créé(s), {upsert_result['updated']} enregistrement(s) mis à jour, {sync_result['updated_count']} emplacement(s) synchronisé(s), {jobs_result['jobs_created']} job(s) créé(s)",
                    'errors': [],
                    'imported_count': upsert_result['created'] + upsert_result['updated'],
                    'imported_created': upsert_result['created'],
                    'imported_updated': upsert_result['updated'],
                    'locations_updated': sync_result['updated_count'],
                    'unconsumed_locations': unconsumed_locations,
                    'unconsumed_locations_count': len(unconsumed_locations),
                    'unconsumed_cleanup': cleanup_stats,
                    'jobs_created': jobs_result['jobs_created'],
                    'job_details_created': jobs_result['job_details_created']
                }
                
        except InventoryLocationJobValidationError as e:
            # Si c'est déjà une erreur de validation, la retourner directement
            logger.error(f"Erreur de validation lors de l'import: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': str(e),
                'errors': [{
                    'row_number': 0,
                    'field': 'validation',
                    'value': '',
                    'message': str(e)
                }],
                'imported_count': 0
            }
        except Exception as e:
            # Pour toute autre exception, la convertir en erreur de validation
            logger.error(f"Erreur lors de l'import: {str(e)}", exc_info=True)
            import traceback
            traceback_str = traceback.format_exc()
            return {
                'success': False,
                'message': f"Erreur lors de l'import: {str(e)}",
                'errors': [{
                    'row_number': 0,
                    'field': 'system',
                    'value': '',
                    'message': f"Erreur système: {str(e)}"
                }],
                'imported_count': 0
            }
    
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
            # Vérifier que le warehouse existe par son nom (warehouse_name)
            try:
                warehouse = self.warehouse_repo.get_by_name(warehouse_value)
            except Exception as e:
                errors.append({
                    'row_number': row_number,
                    'field': 'warehouse',
                    'value': warehouse_value,
                    'message': f"Le warehouse '{warehouse_value}' n'existe pas: {str(e)}"
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
        
        # 3. Validation du job (format JOB-XXXX) - Obligatoire seulement si active = true
        job_value_raw = row_dict.get('job', '')
        # Normaliser les valeurs NaN/pandas en chaîne vide
        if pd.isna(job_value_raw) or str(job_value_raw).lower() in ('nan', 'none', 'null', ''):
            job_value = ''
        else:
            job_value = str(job_value_raw).strip()
        
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
                # Vérifier le format JOB-XXXX (4 chiffres)
                job_pattern = r'^JOB-(\d{4})$'
                match = re.match(job_pattern, job_value)
                if not match:
                    errors.append({
                        'row_number': row_number,
                        'field': 'job',
                        'value': job_value,
                        'message': f"Le format du job '{job_value}' est invalide. Format attendu: JOB-XXXX (ex: JOB-0001, JOB-0002)"
                    })
                else:
                    # Stocker le numéro du job pour la validation d'incrémentation
                    row_dict['job_number'] = int(match.group(1))
        else:
            # Si active = false, job n'est pas obligatoire mais on peut quand même le valider s'il est présent
            if job_value:
                job_pattern = r'^JOB-(\d{4})$'
                match = re.match(job_pattern, job_value)
                if match:
                    # Stocker le numéro du job même si active = false (pour la validation d'incrémentation)
                    row_dict['job_number'] = int(match.group(1))
                else:
                    errors.append({
                        'row_number': row_number,
                        'field': 'job',
                        'value': job_value,
                        'message': f"Le format du job '{job_value}' est invalide. Format attendu: JOB-XXXX (ex: JOB-0001, JOB-0002)"
                    })
        
        # 4. Validation de session_1 (equipe-1001 à equipe-1999) - Obligatoire seulement si active = true
        session_1_value = self._normalize_excel_value(row_dict.get('session_1'))
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
                    if session_number < 1001 or session_number > 1999:
                        errors.append({
                            'row_number': row_number,
                            'field': 'session_1',
                            'value': session_1_value,
                            'message': f"La session_1 '{session_1_value}' est hors plage. Plage attendue: equipe-1001 à equipe-1999"
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
                    if session_number < 1001 or session_number > 1999:
                        errors.append({
                            'row_number': row_number,
                            'field': 'session_1',
                            'value': session_1_value,
                            'message': f"La session_1 '{session_1_value}' est hors plage. Plage attendue: equipe-1001 à equipe-1999"
                        })
        
        # 5. Validation de session_2 (equipe-2001 à equipe-2999) - Obligatoire seulement si active = true
        session_2_value = self._normalize_excel_value(row_dict.get('session_2'))
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
                    if session_number < 2001 or session_number > 2999:
                        errors.append({
                            'row_number': row_number,
                            'field': 'session_2',
                            'value': session_2_value,
                            'message': f"La session_2 '{session_2_value}' est hors plage. Plage attendue: equipe-2001 à equipe-2999"
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
                    if session_number < 2001 or session_number > 2999:
                        errors.append({
                            'row_number': row_number,
                            'field': 'session_2',
                            'value': session_2_value,
                            'message': f"La session_2 '{session_2_value}' est hors plage. Plage attendue: equipe-2001 à equipe-2999"
                        })
        
        # 6. Règle métier supplémentaire :
        #    Si active = false, alors job, session_1 et session_2 doivent être vides.
        #    Sinon, retourner une erreur de validation claire.
        if not is_active:
            if job_value or session_1_value or session_2_value:
                # Erreur pour job si non vide
                if job_value:
                    errors.append({
                        'row_number': row_number,
                        'field': 'job',
                        'value': job_value,
                        'message': "Lorsque le champ 'active' est false, le champ 'job' doit être vide"
                    })
                # Erreur pour session_1 si non vide
                if session_1_value:
                    errors.append({
                        'row_number': row_number,
                        'field': 'session_1',
                        'value': session_1_value,
                        'message': "Lorsque le champ 'active' est false, le champ 'session_1' doit être vide"
                    })
                # Erreur pour session_2 si non vide
                if session_2_value:
                    errors.append({
                        'row_number': row_number,
                        'field': 'session_2',
                        'value': session_2_value,
                        'message': "Lorsque le champ 'active' est false, le champ 'session_2' doit être vide"
                    })
        
        # Stocker is_active dans row_dict pour utilisation ultérieure
        row_dict['is_active'] = is_active
        
        return errors
    
    def _normalize_excel_value(self, value) -> str:
        """
        Normalise une valeur Excel (gère NaN, None, etc.) en chaîne vide
        
        Args:
            value: Valeur à normaliser (peut être NaN, None, 'nan', etc.)
            
        Returns:
            str: Chaîne vide si valeur invalide, sinon la valeur normalisée
        """
        # Vérifier d'abord si c'est NaN pandas/numpy
        try:
            if pd.isna(value):
                return ''
        except (TypeError, ValueError):
            pass
        
        # Vérifier None
        if value is None:
            return ''
        
        # Convertir en string et nettoyer
        value_str = str(value).strip()
        
        # Vérifier les valeurs vides ou invalides
        if not value_str or value_str.lower() in ('nan', 'none', 'null', 'nat', '<na>', 'n/a', 'na'):
            return ''
        
        return value_str
    
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
        
        # Extraire les numéros de jobs uniquement pour les lignes actives, supprimer les doublons et trier
        job_numbers = sorted(set([
            data['job_number'] 
            for data in validated_data 
            if data.get('is_active', False) and 'job_number' in data and data['job_number'] is not None
        ]))
        
        if not job_numbers:
            return errors
        
        # Vérifier l'incrémentation (doit commencer à 1 et être continue)
        if job_numbers[0] != 1:
            errors.append({
                'row_number': 0,  # Erreur globale (0 = pas de ligne spécifique)
                'field': 'job',
                'value': f'JOB-{job_numbers[0]:04d}',
                'message': f"Les jobs doivent commencer à JOB-0001. Premier job trouvé: JOB-{job_numbers[0]:04d}"
            })
            return errors
        
        # Vérifier qu'il n'y a pas de rupture dans l'incrémentation
        expected_number = 1
        for job_number in job_numbers:
            if job_number != expected_number:
                missing_jobs = [f'JOB-{i:04d}' for i in range(expected_number, job_number)]
                errors.append({
                    'row_number': 0,  # Erreur globale (0 = pas de ligne spécifique)
                    'field': 'job',
                    'value': f'JOB-{job_number:04d}',
                    'message': f"Rupture d'incrémentation détectée. Job attendu: JOB-{expected_number:04d}, Job trouvé: JOB-{job_number:04d}. Jobs manquants: {', '.join(missing_jobs) if missing_jobs else 'aucun'}"
                })
                break
            expected_number += 1
        
        return errors
    
    def _validate_job_sessions_consistency(self, validated_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Valide que pour chaque job, toutes les lignes ont exactement les mêmes sessions (session_1 et session_2)
        Ne valide que les lignes où active = true et où job n'est pas vide
        
        Args:
            validated_data: Liste des données validées (contient 'job', 'session_1', 'session_2', 'is_active')
            
        Returns:
            List[Dict]: Liste des erreurs (vide si aucune erreur)
        """
        errors = []
        
        # Filtrer uniquement les lignes actives avec un job
        active_data_with_jobs = [
            data for data in validated_data
            if data.get('is_active', False) and data.get('job')
        ]
        
        if not active_data_with_jobs:
            return errors
        
        # Grouper par job
        from collections import defaultdict
        jobs_sessions = defaultdict(list)
        
        for data in active_data_with_jobs:
            job = data.get('job')
            session_1 = data.get('session_1', '')
            session_2 = data.get('session_2', '')
            row_number = data.get('row_number', 0)
            jobs_sessions[job].append({
                'session_1': session_1,
                'session_2': session_2,
                'row_number': row_number,
            })
        
        # Pour chaque job, vérifier que toutes les sessions sont identiques
        for job, sessions_list in jobs_sessions.items():
            if len(sessions_list) <= 1:
                continue  # Pas besoin de vérifier s'il n'y a qu'une seule ligne
            
            # Récupérer la première session comme référence
            first_session_1 = sessions_list[0]['session_1']
            first_session_2 = sessions_list[0]['session_2']
            first_row_number = sessions_list[0].get('row_number', 0)
            
            # Vérifier que toutes les autres lignes ont les mêmes sessions
            for session_info in sessions_list[1:]:
                if session_info['session_1'] != first_session_1 or session_info['session_2'] != first_session_2:
                    # Utiliser le row_number stocké dans validated_data
                    row_number = session_info.get('row_number', 0)
                    
                    errors.append({
                        'row_number': row_number,
                        'field': 'session',
                        'value': f"session_1={session_info['session_1']}, session_2={session_info['session_2']}",
                        'message': (
                            f"Le job '{job}' doit avoir les mêmes sessions pour toutes ses lignes. "
                            f"Sessions attendues (définies à la ligne {first_row_number}): session_1='{first_session_1}', session_2='{first_session_2}'. "
                            f"Sessions trouvées sur cette ligne: session_1='{session_info['session_1']}', session_2='{session_info['session_2']}'"
                        )
                    })
        
        return errors
    
    def _validate_job_single_team_in_sessions(self, validated_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Valide qu'un job est affecté à une seule équipe dans les deux sessions.
        Cela signifie que session_1 et session_2 doivent correspondre à la même équipe
        (même numéro d'équipe, mais dans des plages différentes: 1001-1999 pour session_1, 2001-2999 pour session_2).
        
        Exemple valide: session_1='equipe-1001', session_2='equipe-2001' (même équipe 1)
        Exemple invalide: session_1='equipe-1001', session_2='equipe-2002' (équipes différentes)
        
        Ne valide que les lignes où active = true et où job n'est pas vide.
        
        Args:
            validated_data: Liste des données validées (contient 'job', 'session_1', 'session_2', 'is_active', 'row_number')
            
        Returns:
            List[Dict]: Liste des erreurs (vide si aucune erreur)
        """
        errors = []
        import re
        
        # Filtrer uniquement les lignes actives avec un job
        active_data_with_jobs = [
            data for data in validated_data
            if data.get('is_active', False) and data.get('job')
        ]
        
        if not active_data_with_jobs:
            return errors
        
        # Pour chaque ligne, vérifier que session_1 et session_2 correspondent à la même équipe
        for data in active_data_with_jobs:
            job = data.get('job')
            session_1 = data.get('session_1', '')
            session_2 = data.get('session_2', '')
            row_number = data.get('row_number', 0)
            
            # Extraire le numéro d'équipe de session_1 (format: equipe-XXXX, plage 1001-1999)
            session_1_pattern = r'^equipe-(\d+)$'
            match_1 = re.match(session_1_pattern, session_1, re.IGNORECASE)
            
            # Extraire le numéro d'équipe de session_2 (format: equipe-XXXX, plage 2001-2999)
            session_2_pattern = r'^equipe-(\d+)$'
            match_2 = re.match(session_2_pattern, session_2, re.IGNORECASE)
            
            # Si les deux sessions sont valides, vérifier qu'elles correspondent à la même équipe
            if match_1 and match_2:
                team_number_1 = int(match_1.group(1))
                team_number_2 = int(match_2.group(1))
                
                # Vérifier que session_1 est dans la plage 1001-1999
                if team_number_1 < 1001 or team_number_1 > 1999:
                    # Cette erreur devrait déjà être détectée par _validate_row, mais on la vérifie quand même
                    continue
                
                # Vérifier que session_2 est dans la plage 2001-2999
                if team_number_2 < 2001 or team_number_2 > 2999:
                    # Cette erreur devrait déjà être détectée par _validate_row, mais on la vérifie quand même
                    continue
                
                # Calculer le numéro d'équipe réel (en soustrayant 1000 pour session_1 et 2000 pour session_2)
                real_team_1 = team_number_1 - 1000
                real_team_2 = team_number_2 - 2000
                
                # Vérifier que les deux sessions correspondent à la même équipe
                if real_team_1 != real_team_2:
                    errors.append({
                        'row_number': row_number,
                        'field': 'session',
                        'value': f"session_1={session_1}, session_2={session_2}",
                        'message': (
                            f"Le job '{job}' doit être affecté à une seule équipe dans les deux sessions. "
                            f"Session 1: '{session_1}' (équipe {real_team_1}), "
                            f"Session 2: '{session_2}' (équipe {real_team_2}). "
                            f"Les deux sessions doivent correspondre à la même équipe. "
                            f"Exemple valide: session_1='equipe-1001' et session_2='equipe-2001' (équipe 1)"
                        )
                    })
        
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

    def _delete_unconsumed_locations(
        self,
        inventory_id: int,
        unconsumed_locations: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Supprime les données (JobDetail, InventoryLocationJob, jobs vides) pour les emplacements
        qui n'apparaissent plus dans le fichier Excel pour un inventaire donné.

        Args:
            inventory_id: ID de l'inventaire
            unconsumed_locations: Liste de dicts retournés par _get_unconsumed_locations

        Returns:
            Dict avec les statistiques de suppression.
        """
        from apps.inventory.models import JobDetail, Job
        from apps.masterdata.models import InventoryLocationJob

        if not unconsumed_locations:
            logger.info(
                f"Aucun emplacement non consommé à supprimer pour l'inventaire {inventory_id}"
            )
            return {
                'deleted_job_details': 0,
                'deleted_location_jobs': 0,
                'deleted_jobs': 0,
            }

        location_ids = [
            loc.get('id') for loc in unconsumed_locations
            if loc.get('id') is not None
        ]

        if not location_ids:
            logger.info(
                f"Aucun ID d'emplacement valide dans la liste des emplacements non consommés "
                f"pour l'inventaire {inventory_id}"
            )
            return {
                'deleted_job_details': 0,
                'deleted_location_jobs': 0,
                'deleted_jobs': 0,
            }

        # 1) Supprimer les JobDetail liés à ces emplacements pour cet inventaire
        jd_qs = JobDetail.objects.filter(
            job__inventory_id=inventory_id,
            location_id__in=location_ids,
        )
        deleted_job_details, _ = jd_qs.delete()

        # 2) Supprimer les liens InventoryLocationJob pour ces emplacements
        ilj_qs = InventoryLocationJob.objects.filter(
            inventaire_id=inventory_id,
            emplacement_id__in=location_ids,
        )
        deleted_location_jobs, _ = ilj_qs.delete()

        # 3) Supprimer les jobs devenus orphelins (sans aucun JobDetail)
        #    pour cet inventaire
        empty_jobs_qs = Job.objects.filter(
            inventory_id=inventory_id
        ).filter(
            jobdetail__isnull=True
        )
        deleted_jobs, _ = empty_jobs_qs.delete()

        logger.info(
            f"Suppression des emplacements non consommés pour l'inventaire {inventory_id}: "
            f"{deleted_job_details} JobDetail supprimé(s), "
            f"{deleted_location_jobs} InventoryLocationJob supprimé(s), "
            f"{deleted_jobs} job(s) supprimé(s)"
        )

        return {
            'deleted_job_details': deleted_job_details,
            'deleted_location_jobs': deleted_location_jobs,
            'deleted_jobs': deleted_jobs,
        }

    def _clear_inventory_jobs(self, inventory_id: int) -> Dict[str, int]:
        """
        Supprime toutes les données de jobs pour un inventaire donné :
        - tous les JobDetail liés aux jobs de cet inventaire
        - tous les InventoryLocationJob de cet inventaire
        - tous les Job de cet inventaire
        """
        from apps.inventory.models import JobDetail, Job
        from apps.masterdata.models import InventoryLocationJob

        # 1) Supprimer tous les JobDetail des jobs de cet inventaire
        jd_qs = JobDetail.objects.filter(job__inventory_id=inventory_id)
        deleted_job_details, _ = jd_qs.delete()

        # 2) Supprimer tous les InventoryLocationJob de cet inventaire
        ilj_qs = InventoryLocationJob.objects.filter(inventaire_id=inventory_id)
        deleted_location_jobs, _ = ilj_qs.delete()

        # 3) Supprimer tous les Jobs de cet inventaire
        jobs_qs = Job.objects.filter(inventory_id=inventory_id)
        deleted_jobs, _ = jobs_qs.delete()

        return {
            'deleted_job_details': deleted_job_details,
            'deleted_location_jobs': deleted_location_jobs,
            'deleted_jobs': deleted_jobs,
        }

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
                """Extrait le numéro du job (ex: JOB-0001 -> 1)"""
                import re
                match = re.match(r'^JOB-(\d{4})$', job_ref)
                return int(match.group(1)) if match else 0
            
            sorted_jobs = sorted(jobs_by_warehouse.keys(), key=lambda x: get_job_number(x[1]))
            
            jobs_created = 0
            job_details_created = 0
            
            # Créer les Jobs et JobDetails pour chaque combinaison warehouse/job
            for warehouse_id, job_reference in sorted_jobs:
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
                    
                    # Vérifier qu'aucun emplacement n'est déjà affecté à un autre job pour cet inventaire.
                    # Si c'est le cas, on considère que c'est une erreur de validation bloquante
                    # (on ne doit PAS ignorer silencieusement cette situation !).
                    existing_job_details = JobDetail.objects.filter(
                        location_id__in=emplacement_ids,
                        job__inventory=inventory
                    ).exclude(job__reference=job_reference)
                    
                    if existing_job_details.exists():
                        conflicting_locations = [
                            jd.location.location_reference
                            for jd in existing_job_details.select_related('location', 'job')
                        ]
                        message = (
                            "Certains emplacements sont déjà affectés à d'autres jobs pour cet inventaire. "
                            f"Job demandé: {job_reference}, Warehouse: {warehouse.warehouse_name}. "
                            f"Emplacements en conflit: {', '.join(conflicting_locations)}"
                        )
                        logger.error(message)
                        # On lève une erreur de validation pour annuler TOUT l'import
                        # et remonter une information claire à l'utilisateur.
                        raise InventoryLocationJobValidationError(message)
                    
                    # Créer le Job avec la référence du fichier Excel
                    job = Job.objects.create(
                        reference=job_reference,  # Utiliser la référence du fichier Excel (ex: JOB-0001)
                        status='EN ATTENTE',
                        en_attente_date=timezone.now(),
                        warehouse=warehouse,
                        inventory=inventory
                    )
                    jobs_created += 1
                    logger.info(f"Job {job.reference} créé pour l'inventaire {inventory.reference} et le warehouse {warehouse.warehouse_name}")
                    
                    # Créer les JobDetails selon la logique des comptages.
                    # IMPORTANT : en cas d'erreur dans la création des JobDetails,
                    # _create_job_details_for_job lèvera une InventoryLocationJobValidationError,
                    # ce qui fera échouer toute la transaction (comportement "tout ou rien").
                    details_count = self._create_job_details_for_job(
                        job, locations, counting1, counting2
                    )
                    job_details_created += details_count
            
            return {
                'jobs_created': jobs_created,
                'job_details_created': job_details_created
            }
            
        except InventoryLocationJobValidationError:
            # Laisser remonter l'erreur de validation pour qu'elle annule l'import complet
            raise
        except Exception as e:
            # Toute autre erreur technique est convertie en erreur de validation
            logger.error(f"Erreur lors de la création des jobs et job details: {str(e)}", exc_info=True)
            raise InventoryLocationJobValidationError(
                f"Erreur lors de la création des jobs et job details: {str(e)}"
            )
    
    def _create_job_details_for_job(
        self,
        job: Job,
        locations: List[Location],
        counting1: Counting,
        counting2: Counting
    ) -> int:
        """
        Crée ou met à jour les JobDetails pour un job selon la logique des comptages (UPSERT)
        Clé unique : (job_id, location_id, counting_id)
        
        Args:
            job: Le job pour lequel créer/mettre à jour les JobDetails
            locations: Liste des emplacements (déjà triés)
            counting1: Premier comptage
            counting2: Deuxième comptage
            
        Returns:
            int: Nombre de JobDetails créés/mis à jour
        """
        details_count = 0
        
        # Récupérer les JobDetails existants pour ce job
        location_ids = [loc.id for loc in locations]
        existing_job_details = JobDetail.objects.filter(
            job=job,
            location_id__in=location_ids
        ).select_related('counting')
        
        # Créer un dictionnaire pour un accès rapide : (location_id, counting_id) -> JobDetail
        existing_map = {
            (jd.location_id, jd.counting_id): jd
            for jd in existing_job_details
        }
        
        # Préparer les objets à créer et à mettre à jour
        objects_to_create = []
        objects_to_update = []
        
        if counting1.count_mode == "image de stock":
            # Cas 1: 1er comptage = image de stock
            # Créer/mettre à jour les emplacements seulement pour le 2ème comptage
            logger.debug(f"Configuration 'image de stock' détectée pour le job {job.reference}")
            
            for location in locations:
                key = (location.id, counting2.id)
                existing_jd = existing_map.get(key)
                
                if existing_jd:
                    # Mettre à jour l'existant
                    existing_jd.status = 'EN ATTENTE'
                    existing_jd.en_attente_date = timezone.now()
                    objects_to_update.append(existing_jd)
                else:
                    # Créer un nouveau (la référence sera auto‑générée par le modèle)
                    objects_to_create.append(JobDetail(
                        location=location,
                        job=job,
                        counting=counting2,  # Assigner au 2ème comptage
                        status='EN ATTENTE',
                        en_attente_date=timezone.now()
                    ))
                details_count += 1
        else:
            # Cas 2: 1er comptage différent de "image de stock"
            # Dupliquer les emplacements pour les deux comptages
            logger.debug(f"Configuration normale détectée pour le job {job.reference}")
            
            for location in locations:
                # JobDetail pour le 1er comptage
                key1 = (location.id, counting1.id)
                existing_jd1 = existing_map.get(key1)
                
                if existing_jd1:
                    existing_jd1.status = 'EN ATTENTE'
                    existing_jd1.en_attente_date = timezone.now()
                    objects_to_update.append(existing_jd1)
                else:
                    objects_to_create.append(JobDetail(
                        location=location,
                        job=job,
                        counting=counting1,
                        status='EN ATTENTE',
                        en_attente_date=timezone.now()
                    ))
                details_count += 1
                
                # JobDetail pour le 2ème comptage
                key2 = (location.id, counting2.id)
                existing_jd2 = existing_map.get(key2)
                
                if existing_jd2:
                    existing_jd2.status = 'EN ATTENTE'
                    existing_jd2.en_attente_date = timezone.now()
                    objects_to_update.append(existing_jd2)
                else:
                    objects_to_create.append(JobDetail(
                        location=location,
                        job=job,
                        counting=counting2,
                        status='EN ATTENTE',
                        en_attente_date=timezone.now()
                    ))
                details_count += 1
        
        # Effectuer les opérations en masse
        try:
            if objects_to_create:
                # Générer les références et vérifier les doublons
                existing_references = set(
                    JobDetail.objects.filter(
                        reference__in=[obj.reference for obj in objects_to_create if obj.reference]
                    ).values_list('reference', flat=True)
                )
                
                # Régénérer les références pour les objets qui ont des doublons
                for obj in objects_to_create:
                    if obj.reference and obj.reference in existing_references:
                        # Régénérer la référence jusqu'à ce qu'elle soit unique
                        max_attempts = 10
                        attempt = 0
                        while attempt < max_attempts:
                            new_reference = JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX)
                            if not JobDetail.objects.filter(reference=new_reference).exists():
                                obj.reference = new_reference
                                existing_references.add(new_reference)
                                break
                            attempt += 1
                        else:
                            # Si on n'a pas réussi après 10 tentatives, utiliser un UUID complet
                            import uuid
                            obj.reference = f"{JobDetail.REFERENCE_PREFIX}-{uuid.uuid4().hex[:16].upper()}"
                
                # Créer / mettre à jour les objets un par un.
                # En cas d'erreur sur un seul JobDetail, on lève une erreur de validation
                # pour forcer le rollback de toute la transaction (comportement tout ou rien).
                for obj in objects_to_create:
                    # Vérifier si un JobDetail existe déjà avec cette combinaison (job, location, counting)
                    existing_by_key = JobDetail.objects.filter(
                        job=obj.job,
                        location=obj.location,
                        counting=obj.counting
                    ).first()
                    
                    if existing_by_key:
                        # Mettre à jour l'existant au lieu de créer un nouveau
                        existing_by_key.status = obj.status
                        existing_by_key.en_attente_date = obj.en_attente_date
                        existing_by_key.save(update_fields=['status', 'en_attente_date', 'updated_at'])
                        logger.debug(
                            f"JobDetail existant mis à jour pour job={obj.job.reference}, "
                            f"location={obj.location.location_reference}, counting={obj.counting.reference}"
                        )
                    else:
                        # Générer une référence unique si elle est absente / vide
                        if not getattr(obj, 'reference', None):
                            max_attempts = 10
                            for attempt in range(max_attempts):
                                new_ref = JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX)
                                if not JobDetail.objects.filter(reference=new_ref).exists():
                                    obj.reference = new_ref
                                    break
                            else:
                                raise InventoryLocationJobValidationError(
                                    "Impossible de générer une référence unique pour un JobDetail"
                                )
                        obj.save()
                    # Chaque création/mise à jour compte pour 1 détail
                    # (on a déjà incrémenté details_count plus haut)
            
            if objects_to_update:
                JobDetail.objects.bulk_update(
                    objects_to_update,
                    ['status', 'en_attente_date', 'updated_at']
                )
        
        except Exception as e:
            logger.error(
                f"Erreur lors de la création ou mise à jour des JobDetail pour le job {job.reference}: {str(e)}",
                exc_info=True
            )
            # Faire échouer l'import complet
            raise InventoryLocationJobValidationError(
                f"Erreur lors de la création ou mise à jour des JobDetail pour le job {job.reference}: {str(e)}"
            )
        
        return details_count

