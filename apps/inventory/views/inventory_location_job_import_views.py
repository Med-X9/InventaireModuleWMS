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
        - warehouse: Référence du warehouse
        - emplacement: Référence de l'emplacement
        - active: (utilisé pour synchroniser Location.is_active)
        - job: Format job-XX (ex: job-01, job-02, ...)
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
                
                # Lancer l'import asynchrone
                self.service.import_from_excel_async(
                    inventory_id=inventory_id,
                    file_path=file_path,
                    callback=import_callback
                )
                
                # Retourner immédiatement une réponse indiquant que le traitement est en cours
                return self._success_response(
                    data={
                        'status': 'processing',
                        'message': 'Import en cours de traitement. Le traitement est effectué en arrière-plan.',
                        'inventory_id': inventory_id
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

