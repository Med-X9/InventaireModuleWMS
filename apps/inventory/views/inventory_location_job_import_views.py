"""
Vues pour l'import des InventoryLocationJob
"""
import logging
import tempfile
import os
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.inventory.services.inventory_location_job_import_service import InventoryLocationJobImportService
from apps.inventory.serializers.inventory_location_job_import_serializer import InventoryLocationJobImportSerializer
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
        - session_1: Format equipe-XXXX (plage: 1000-1999)
        - session_2: Format equipe-XXXX (plage: 2000-2999)
        """
        try:
            # Valider le serializer
            serializer = InventoryLocationJobImportSerializer(data=request.data)
            if not serializer.is_valid():
                return self._error_response(
                    message="Erreur de validation du fichier",
                    errors=serializer.errors,
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
                return self._success_response(
                    data={
                        'status': 'processing',
                        'message': 'Import en cours de traitement. Le traitement est effectué en arrière-plan.',
                        'inventory_id': inventory_id,
                        'import_task_id': import_task.id
                    },
                    status_code=status.HTTP_202_ACCEPTED
                )
                
            finally:
                # Nettoyer le fichier temporaire après un délai (ou le laisser pour le traitement asynchrone)
                # Pour l'instant, on le laisse pour le traitement asynchrone
                # Il sera nettoyé après le traitement
                pass
                
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé: {str(e)}")
            return self._error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except InventoryLocationJobValidationError as e:
            logger.warning(f"Erreur de validation: {str(e)}")
            return self._error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'import: {str(e)}", exc_info=True)
            return self._error_response(
                message=f"Erreur lors de l'import: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _success_response(self, data, message=None, status_code=status.HTTP_200_OK):
        """Helper pour créer une réponse de succès"""
        from rest_framework.response import Response
        response_data = {
            'success': True,
            'message': message or 'Opération réussie',
            'data': data
        }
        return Response(response_data, status=status_code)
    
    def _error_response(self, message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """Helper pour créer une réponse d'erreur"""
        from rest_framework.response import Response
        response_data = {
            'success': False,
            'message': message,
            'errors': errors or []
        }
        return Response(response_data, status=status_code)


class InventoryLocationJobImportSyncView(APIView):
    """
    Vue pour importer des InventoryLocationJob depuis un fichier Excel (version synchrone)
    Utile pour les tests ou les petits fichiers
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryLocationJobImportService()
    
    def post(self, request, inventory_id, *args, **kwargs):
        """
        Importe des InventoryLocationJob depuis un fichier Excel (synchrone)
        """
        try:
            # Valider le serializer
            serializer = InventoryLocationJobImportSerializer(data=request.data)
            if not serializer.is_valid():
                return self._error_response(
                    message="Erreur de validation du fichier",
                    errors=serializer.errors,
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
                
                # Lancer l'import de manière synchrone
                result = self.service.import_from_excel(
                    inventory_id=inventory_id,
                    file_path=file_path
                )
                
                # Préparer la réponse
                if result['success']:
                    return self._success_response(
                        data={
                            'imported_count': result['imported_count'],
                            'locations_updated': result.get('locations_updated', 0),
                            'jobs_created': result.get('jobs_created', 0),
                            'job_details_created': result.get('job_details_created', 0),
                            'unconsumed_locations_count': result.get('unconsumed_locations_count', 0),
                            'message': result['message']
                        },
                        message=result['message'],
                        status_code=status.HTTP_201_CREATED
                    )
                else:
                    return self._error_response(
                        message=result['message'],
                        errors=result.get('errors', []),
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                    
            finally:
                # Nettoyer le fichier temporaire
                if os.path.exists(file_path):
                    os.unlink(file_path)
                
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé: {str(e)}")
            return self._error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except InventoryLocationJobValidationError as e:
            logger.warning(f"Erreur de validation: {str(e)}")
            return self._error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'import: {str(e)}", exc_info=True)
            return self._error_response(
                message=f"Erreur lors de l'import: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _success_response(self, data, message=None, status_code=status.HTTP_200_OK):
        """Helper pour créer une réponse de succès"""
        from rest_framework.response import Response
        response_data = {
            'success': True,
            'message': message or 'Opération réussie',
            'data': data
        }
        return Response(response_data, status=status_code)
    
    def _error_response(self, message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """Helper pour créer une réponse d'erreur"""
        from rest_framework.response import Response
        response_data = {
            'success': False,
            'message': message,
            'errors': errors or []
        }
        return Response(response_data, status=status_code)


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
                return self._error_response(
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
            
            return self._success_response(
                data={
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
                },
                message=f"Statut de l'import: {import_task.get_status_display()}",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {str(e)}", exc_info=True)
            return self._error_response(
                message=f"Erreur lors de la récupération du statut: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _success_response(self, data, message=None, status_code=status.HTTP_200_OK):
        """Helper pour créer une réponse de succès"""
        from rest_framework.response import Response
        response_data = {
            'success': True,
            'message': message or 'Opération réussie',
            'data': data
        }
        return Response(response_data, status=status_code)
    
    def _error_response(self, message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """Helper pour créer une réponse d'erreur"""
        from rest_framework.response import Response
        response_data = {
            'success': False,
            'message': message,
            'errors': errors or []
        }
        return Response(response_data, status=status_code)
