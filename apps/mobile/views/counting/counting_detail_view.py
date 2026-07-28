"""
Vue pour la gestion des CountingDetail et NumeroSerie.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.inventory.models import Job
from apps.mobile.services.counting_detail_service import CountingDetailService
from apps.mobile.usecases.counting_detail_ecart_final_result import (
    CountingDetailEcartFinalResultUseCase,
)
from apps.mobile.utils import success_response, error_response
from apps.mobile.exceptions import (
    CountingDetailValidationError,
    ProductPropertyValidationError,
    CountingAssignmentValidationError,
    JobDetailValidationError,
    NumeroSerieValidationError,
    CountingModeValidationError,
    EcartComptageResoluError
)
import logging

logger = logging.getLogger(__name__)

class CountingDetailView(APIView):
    """
    Vue pour la création de CountingDetail et NumeroSerie.
    
    URL: /mobile/api/job/<job_id>/counting-detail/

    final_result (EcartComptage) — Strategy selon inventory_type du job :
    - MAGASIN / TOURNANT : final_result = quantité comptée (1er envoi)
    - GENERAL : consensus multi-comptages (≥ 2 séquences, logique existante)
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.counting_detail_service = CountingDetailService()
        self.ecart_final_result_use_case = CountingDetailEcartFinalResultUseCase()
    
    def _handle_exception(self, e, error_type=None):
        """
        Gère les exceptions communes et retourne une réponse appropriée.
        """
        if isinstance(e, CountingDetailValidationError):
            logger.warning(f"Erreur de validation des données: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='validation_error'
            )
            
        elif isinstance(e, ProductPropertyValidationError):
            logger.warning(f"Erreur de validation des propriétés du produit: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='product_property_error'
            )
            
        elif isinstance(e, CountingAssignmentValidationError):
            logger.warning(f"Erreur de validation de l'assignment: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='assignment_error'
            )
            
        elif isinstance(e, JobDetailValidationError):
            logger.warning(f"Erreur de validation du JobDetail: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='job_detail_error'
            )
            
        elif isinstance(e, NumeroSerieValidationError):
            logger.warning(f"Erreur de validation des numéros de série: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='numero_serie_error'
            )
            
        elif isinstance(e, CountingModeValidationError):
            logger.warning(f"Erreur de validation du mode de comptage: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='counting_mode_error'
            )
            
        elif isinstance(e, EcartComptageResoluError):
            logger.warning(f"Tentative d'ajout à un écart résolu: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='ecart_resolu_error',
                ecart_reference=e.ecart.reference if hasattr(e, 'ecart') and e.ecart else None
            )
        
        else:
            logger.error(f"Erreur interne: {str(e)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue s'est produite lors du traitement",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, job_id=None):
        """
        Crée plusieurs CountingDetail et leurs NumeroSerie associés en lot.
        L'API traite toujours en lot, même pour un seul élément.
        
        Format de requête (tableau directement, ou objet unique converti automatiquement):
        [
            {
                "counting_id": 1,
                "location_id": 1,
                "quantity_inventoried": 10,
                "assignment_id": 1,
                "product_id": 1,
                "dlc": "2024-12-31",
                "n_lot": "LOT123",
                "numeros_serie": [{"n_serie": "NS001"}]
            },
            {
                "counting_id": 1,
                "location_id": 2,
                "quantity_inventoried": 5,
                "assignment_id": 1,
                "product_id": 2
            }
        ]
        
        Note: Les ComptageSequence sont créées automatiquement pour chaque CountingDetail.
        L'EcartComptage est détecté/créé automatiquement basé sur :
        - product_id + location_id + inventory (du job)
        Si un écart existe déjà pour cette combinaison et est résolu, une erreur sera levée.
        final_result est calculé via Strategy selon le type d'inventaire (voir doc classe).
        """
        try:
            if not job_id:
                return error_response(
                    message="job_id est obligatoire dans l'URL",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            try:
                inventory_context = self.ecart_final_result_use_case.get_context_for_job(
                    job_id
                )
            except Job.DoesNotExist:
                return error_response(
                    message=f"Job {job_id} introuvable",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            logger.info(
                "CountingDetail job_id=%s type=%s strategy=%s items=%s",
                job_id,
                inventory_context.get("inventory_type"),
                inventory_context.get("final_result_strategy"),
                len(request.data) if isinstance(request.data, list) else 1,
            )
            
            # Normaliser les données : toujours traiter comme un tableau
            if isinstance(request.data, list):
                data_list = request.data
            elif isinstance(request.data, dict) and 'data' in request.data:
                data_list = request.data['data']
            elif isinstance(request.data, dict):
                # Si un seul objet est envoyé, le convertir en tableau
                data_list = [request.data]
            else:
                return error_response(
                    message='Les données doivent être un tableau ou un objet',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if not data_list:
                return error_response(
                    message='La liste de données est vide',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Valider que tous les assignment_id appartiennent au job_id
            assignment_ids = [item.get('assignment_id') for item in data_list if item.get('assignment_id')]
            if assignment_ids:
                self.counting_detail_service.validate_assignments_belong_to_job(job_id, assignment_ids)
            
            # Traitement en lot optimisé (toujours en lot)
            result = self.counting_detail_service.create_counting_details_batch(data_list, job_id=job_id)
            
            # Vérifier si le traitement a réussi
            if not result.get('success', False):
                # Si des erreurs sont présentes, retourner 500
                logger.error(f"Échec de la création en lot: {result.get('message', 'Erreur inconnue')}")
                return error_response(
                    message=result.get('message', 'Erreur lors de la création en lot'),
                    errors=result.get('errors', []),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return success_response(
                data={
                    **result,
                    "inventory_context": result.get(
                        "inventory_context", inventory_context
                    ),
                },
                message="Comptages créés avec succès",
                status_code=status.HTTP_201_CREATED,
            )
            
        except Exception as e:
            return self._handle_exception(e)


