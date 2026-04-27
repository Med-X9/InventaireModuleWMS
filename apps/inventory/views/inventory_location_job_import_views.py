"""
Vues pour l'import des InventoryLocationJob
"""
import logging
import tempfile
import os
import pandas as pd
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.inventory.services.inventory_location_job_import_service import InventoryLocationJobImportService
from apps.inventory.serializers.inventory_location_job_import_serializer import InventoryLocationJobImportSerializer
from apps.inventory.utils.response_utils import success_response, error_response, validation_error_response
from apps.masterdata.exceptions import InventoryLocationJobValidationError
from apps.inventory.exceptions import InventoryNotFoundError
from apps.masterdata.models import ImportTask, ImportError

logger = logging.getLogger(__name__)


class InventoryLocationJobImportView(APIView):
    """
    Vue pour importer des InventoryLocationJob depuis un fichier Excel
    Traitement asynchrone sans Celery
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryLocationJobImportService()
    
    def post(self, request, inventory_id, *args, **kwargs):
        """
        Importe des InventoryLocationJob depuis un fichier Excel pour un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            request.FILES['file']: Le fichier Excel à importer
            
        Format attendu du fichier Excel:
        - Colonnes requises: warehouse, emplacement, active, job, session_1, session_2
        - warehouse: Nom du warehouse (warehouse_name)
        - emplacement: Référence de l'emplacement
        - active: (utilisé pour synchroniser Location.is_active)
        - job: Format JOB-XXXX (ex: JOB-0001, JOB-0002, ...)
        - session_1: Format equipe-XXXX (plage: 1001-1999)
        - session_2: Format equipe-XXXX (plage: 2001-2999)
        """
        try:
            # Valider le serializer
            serializer = InventoryLocationJobImportSerializer(data=request.data)
            if not serializer.is_valid():
                return validation_error_response(
                    serializer.errors,
                    message="Erreur de validation du fichier",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            excel_file = serializer.validated_data['file']
            
            # Sauvegarder le fichier temporairement
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            try:
                for chunk in excel_file.chunks():
                    temp_file.write(chunk)
                temp_file.close()
                file_path = temp_file.name
                
                # Lancer l'import de manière asynchrone
                def import_callback(result):
                    """Callback appelé après l'import"""
                    # Nettoyer le fichier temporaire après le traitement
                    try:
                        if os.path.exists(file_path):
                            os.unlink(file_path)
                            logger.info(f"Fichier temporaire supprimé: {file_path}")
                    except Exception as e:
                        logger.warning(f"Erreur lors de la suppression du fichier temporaire: {str(e)}")
                    
                    logger.info(f"Import terminé pour l'inventaire {inventory_id}: {result.get('message', '')}")
                
                # Récupérer l'ID de l'utilisateur connecté
                user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
                
                # Lancer l'import asynchrone et récupérer l'ImportTask
                import_task = self.service.import_from_excel_async(
                    inventory_id=inventory_id,
                    file_path=file_path,
                    user_id=user_id,
                    callback=import_callback
                )
                
                # Retourner immédiatement une réponse indiquant que le traitement est en cours
                return success_response(
                    data={
                        'status': 'processing',
                        'message': 'Import en cours de traitement. Le traitement est effectué en arrière-plan.',
                        'inventory_id': inventory_id,
                        'import_task_id': import_task.id
                    },
                    message='Import en cours de traitement. Le traitement est effectué en arrière-plan.',
                    status_code=status.HTTP_202_ACCEPTED
                )
                
            finally:
                # Nettoyer le fichier temporaire après un délai (ou le laisser pour le traitement asynchrone)
                # Pour l'instant, on le laisse pour le traitement asynchrone
                # Il sera nettoyé après le traitement
                pass
                
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except InventoryLocationJobValidationError as e:
            logger.warning(f"Erreur de validation: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'import: {str(e)}", exc_info=True)
            return error_response(
                message=f"Erreur lors de l'import: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class InventoryLocationJobImportSyncView(APIView):
    """
    Vue pour importer des InventoryLocationJob depuis un fichier Excel (version asynchrone)
    Retourne immédiatement une réponse avec import_task_id, le traitement se fait en arrière-plan
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryLocationJobImportService()
    
    def post(self, request, inventory_id, *args, **kwargs):
        """
        Importe des InventoryLocationJob depuis un fichier Excel (asynchrone)
        Retourne immédiatement avec un import_task_id, le traitement se fait en arrière-plan
        """
        try:
            # Valider le serializer
            serializer = InventoryLocationJobImportSerializer(data=request.data)
            if not serializer.is_valid():
                return validation_error_response(
                    serializer.errors,
                    message="Erreur de validation du fichier",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            excel_file = serializer.validated_data['file']
            
            # Extraire le nom de fichier
            file_name = excel_file.name if hasattr(excel_file, 'name') else 'fichier.xlsx'
            
            # Sauvegarder le fichier temporairement
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            try:
                for chunk in excel_file.chunks():
                    temp_file.write(chunk)
                temp_file.close()
                file_path = temp_file.name
                
                # Lire le fichier Excel pour extraire les colonnes et le nombre de lignes
                try:
                    df = pd.read_excel(file_path, engine='openpyxl')
                    # Normaliser les noms de colonnes (minuscules, sans espaces) comme dans le service
                    df.columns = df.columns.str.strip().str.lower()
                    columns = list(df.columns)
                    total_rows = len(df)
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du fichier Excel: {str(e)}")
                    return error_response(
                        message=f"Erreur lors de la lecture du fichier Excel: {str(e)}",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                # Valider la structure du fichier (colonnes requises)
                required_columns = ['warehouse', 'emplacement', 'active', 'job', 'session_1', 'session_2']
                missing_columns = [col for col in required_columns if col not in columns]
                
                if missing_columns:
                    # Nettoyer le fichier temporaire avant de retourner l'erreur
                    try:
                        if os.path.exists(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        logger.warning(f"Erreur lors de la suppression du fichier temporaire: {str(e)}")
                    
                    return error_response(
                        message=f"Colonnes manquantes dans le fichier Excel: {', '.join(missing_columns)}",
                        status_code=status.HTTP_400_BAD_REQUEST,
                        data={
                            'missing_columns': missing_columns,
                            'required_columns': required_columns,
                            'found_columns': columns,
                            'file_name': file_name,
                            'total_rows': total_rows
                        }
                    )
                
                # Lancer l'import de manière asynchrone
                def import_callback(result):
                    """Callback appelé après l'import"""
                    # Nettoyer le fichier temporaire après le traitement
                    try:
                        if os.path.exists(file_path):
                            os.unlink(file_path)
                            logger.info(f"Fichier temporaire supprimé: {file_path}")
                    except Exception as e:
                        logger.warning(f"Erreur lors de la suppression du fichier temporaire: {str(e)}")
                    
                    logger.info(f"Import terminé pour l'inventaire {inventory_id}: {result.get('message', '')}")
                
                # Récupérer l'ID de l'utilisateur connecté
                user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
                
                # Lancer l'import asynchrone et récupérer l'ImportTask
                import_task = self.service.import_from_excel_async(
                    inventory_id=inventory_id,
                    file_path=file_path,
                    user_id=user_id,
                    callback=import_callback
                )
                
                # Retourner immédiatement une réponse indiquant que le traitement est en cours
                return success_response(
                    data={
                        'status': 'processing',
                        'message': 'Import en cours de traitement. Le traitement est effectué en arrière-plan.',
                        'inventory_id': inventory_id,
                        'import_task_id': import_task.id,
                        'file_name': file_name,
                        'columns': columns,
                        'total_rows': total_rows
                    },
                    message='Import en cours de traitement. Le traitement est effectué en arrière-plan.',
                    status_code=status.HTTP_202_ACCEPTED
                )
                    
            finally:
                # Le fichier temporaire sera nettoyé après le traitement asynchrone via le callback
                pass
                
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except InventoryLocationJobValidationError as e:
            logger.warning(f"Erreur de validation: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'import: {str(e)}", exc_info=True)
            return error_response(
                message=f"Erreur lors de l'import: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class InventoryLocationJobImportStatusView(APIView):
    """
    Vue pour récupérer le statut et les erreurs d'un import
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, inventaire_id, *args, **kwargs):
        """
        Récupère le statut et les erreurs d'un import pour un inventaire donné
        
        Args:
            inventaire_id: ID de l'inventaire
        """
        try:
            # Récupérer la dernière ImportTask pour cet inventaire
            import_task = ImportTask.objects.filter(inventory_id=inventaire_id).order_by('-created_at').first()
            
            if not import_task:
                return error_response(
                    message=f"Aucune tâche d'import trouvée pour l'inventaire {inventaire_id}",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Récupérer les erreurs associées
            errors = ImportError.objects.filter(import_task=import_task).order_by('row_number')
            errors_data = [
                {
                    'row_number': error.row_number,
                    'error_type': error.error_type,
                    'error_message': error.error_message,
                    'field_name': error.field_name,
                    'field_value': error.field_value,
                    'row_data': error.row_data
                }
                for error in errors
            ]
            
            # Récupérer la progression des chunks
            chunks_progress = import_task.get_chunks_progress()
            chunks_data = []
            completed_chunks = 0
            current_chunk = None
            
            if chunks_progress:
                for chunk in chunks_progress:
                    chunk_size = chunk.get('end_row', 0) - chunk.get('start_row', 0) + 1
                    progress = 0.0
                    
                    if chunk.get('status') == 'COMPLETED':
                        progress = 100.0
                        completed_chunks += 1
                    elif chunk.get('status') == 'PROCESSING':
                        progress = (chunk.get('processed_rows', 0) / chunk_size * 100) if chunk_size > 0 else 0
                        if not current_chunk:
                            current_chunk = chunk.get('chunk_number')
                    
                    chunks_data.append({
                        'chunk_number': chunk.get('chunk_number'),
                        'status': chunk.get('status'),
                        'start_row': chunk.get('start_row'),
                        'end_row': chunk.get('end_row'),
                        'processed_rows': chunk.get('processed_rows', 0),
                        'imported_count': chunk.get('imported_count', 0),
                        'updated_count': chunk.get('updated_count', 0),
                        'error_count': chunk.get('error_count', 0),
                        'progress': round(progress, 2),
                        'started_at': chunk.get('started_at'),
                        'completed_at': chunk.get('completed_at'),
                        'error_message': chunk.get('error_message')
                    })
            
            # Calculer la progression globale
            total_chunks = len(chunks_data)
            overall_progress = (completed_chunks / total_chunks * 100) if total_chunks > 0 else 0
            
            response_data = {
                'import_task_id': import_task.id,
                'inventory_id': inventaire_id,
                'status': import_task.status,
                'file_name': import_task.file_name,
                'total_rows': import_task.total_rows,
                'validated_rows': import_task.validated_rows,
                'processed_rows': import_task.processed_rows,
                'imported_count': import_task.imported_count,
                'updated_count': import_task.updated_count,
                'error_count': import_task.error_count,
                'error_message': import_task.error_message,
                'errors': errors_data,
                'created_at': import_task.created_at,
                'updated_at': import_task.updated_at
            }
            
            # Ajouter les informations sur les chunks si disponibles
            if chunks_data:
                response_data['chunks'] = {
                    'total_chunks': total_chunks,
                    'completed_chunks': completed_chunks,
                    'current_chunk': current_chunk,
                    'overall_progress': round(overall_progress, 2),
                    'chunks_detail': chunks_data
                }
            
            return success_response(
                data=response_data,
                message=f"Statut de l'import: {import_task.get_status_display()}",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {str(e)}", exc_info=True)
            return error_response(
                message=f"Erreur lors de la récupération du statut: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
