"""
Vue pour la gestion des CountingDetail et NumeroSerie.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.counting_detail_service import CountingDetailService
from apps.mobile.exceptions import (
    CountingDetailValidationError,
    ProductPropertyValidationError,
    CountingAssignmentValidationError,
    JobDetailValidationError,
    NumeroSerieValidationError,
    CountingModeValidationError
)
import logging

logger = logging.getLogger(__name__)

class CountingDetailView(APIView):
    """
    Vue pour la création de CountingDetail et NumeroSerie.
    
    URL: /mobile/api/counting-detail/
    """
    permission_classes = [IsAuthenticated]  # Réactivé maintenant que le problème est corrigé
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.counting_detail_service = CountingDetailService()
    
    def _handle_exception(self, e, error_type=None):
        """
        Gère les exceptions communes et retourne une réponse appropriée.
        """
        if isinstance(e, CountingDetailValidationError):
            logger.warning(f"Erreur de validation des données: {str(e)}")
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'validation_error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        elif isinstance(e, ProductPropertyValidationError):
            logger.warning(f"Erreur de validation des propriétés du produit: {str(e)}")
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'product_property_error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        elif isinstance(e, CountingAssignmentValidationError):
            logger.warning(f"Erreur de validation de l'assignment: {str(e)}")
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'assignment_error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        elif isinstance(e, JobDetailValidationError):
            logger.warning(f"Erreur de validation du JobDetail: {str(e)}")
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'job_detail_error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        elif isinstance(e, NumeroSerieValidationError):
            logger.warning(f"Erreur de validation des numéros de série: {str(e)}")
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'numero_serie_error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        elif isinstance(e, CountingModeValidationError):
            logger.warning(f"Erreur de validation du mode de comptage: {str(e)}")
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'counting_mode_error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        else:
            logger.error(f"Erreur interne: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': f'Erreur interne: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _serialize_counting_detail(self, cd):
        """
        Sérialise un objet CountingDetail en dictionnaire.
        """
        return {
            'id': cd.id,
            'reference': cd.reference,
            'quantity_inventoried': cd.quantity_inventoried,
            'product_id': cd.product.id if cd.product else None,
            'location_id': cd.location.id,
            'counting_id': cd.counting.id,
            'created_at': cd.created_at,
            'numeros_serie': [
                {
                    'id': ns.id,
                    'n_serie': ns.n_serie,
                    'reference': ns.reference
                } for ns in self.counting_detail_service.get_numeros_serie_by_counting_detail(cd.id)
            ]
        }
    
    def _create_success_response(self, data, status_code=status.HTTP_200_OK):
        """
        Crée une réponse de succès standardisée.
        """
        return Response({
            'success': True,
            'data': data
        }, status=status_code)
    
    def _create_error_response(self, error_message, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Crée une réponse d'erreur standardisée.
        """
        return Response({
            'success': False,
            'error': error_message
        }, status=status_code)
    
    def post(self, request):
        """
        Crée un ou plusieurs CountingDetail et leurs NumeroSerie associés.
        
        Pour un seul enregistrement:
        {
            "counting_id": 1,                    # Obligatoire
            "location_id": 1,                    # Obligatoire
            "quantity_inventoried": 10,          # Obligatoire
            "assignment_id": 1,                  # Obligatoire (pour récupérer le JobDetail)
            "product_id": 1,                     # Optionnel (selon le mode de comptage)
            "dlc": "2024-12-31",                # Optionnel
            "n_lot": "LOT123",                  # Optionnel
            "numeros_serie": [                   # Optionnel (si n_serie activé)
                {"n_serie": "NS001"},
                {"n_serie": "NS002"}
            ]
        }
        
        Pour plusieurs enregistrements (mode lot):
        {
            "batch": true,
            "data": [
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
        }
        """
        try:
            logger.info(f"Traitement de CountingDetail avec les données: {request.data}")
            
            # Vérifier si c'est un traitement en lot
            if request.data.get('batch', False):
                # Traitement en lot
                data_list = request.data.get('data', [])
                if not data_list:
                    return self._create_error_response(
                        'La liste de données est vide pour le traitement en lot'
                    )
                
                result = self.counting_detail_service.create_counting_details_batch(data_list)
                return self._create_success_response(result, status.HTTP_201_CREATED)
                
            else:
                # Traitement d'un seul enregistrement
                result = self.counting_detail_service.create_counting_detail(request.data)
                return self._create_success_response(result, status.HTTP_201_CREATED)
            
        except Exception as e:
            return self._handle_exception(e)
    
    def put(self, request):
        """
        Valide plusieurs CountingDetail sans les créer (validation en lot).
        
        Body requis:
        {
            "data": [
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
        }
        """
        try:
            logger.info(f"Validation en lot de CountingDetail avec les données: {request.data}")
            
            data_list = request.data.get('data', [])
            if not data_list:
                return self._create_error_response(
                    'La liste de données est vide pour la validation'
                )
            
            # Valider les enregistrements en lot
            result = self.counting_detail_service.validate_counting_details_batch(data_list)
            return self._create_success_response(result)
            
        except Exception as e:
            return self._handle_exception(e)
    
    def get(self, request):
        """
        Récupère des informations sur les CountingDetail.
        
        Query params:
        - counting_id: ID du comptage
        - location_id: ID de l'emplacement
        - product_id: ID du produit
        """
        try:
            counting_id = request.query_params.get('counting_id')
            location_id = request.query_params.get('location_id')
            product_id = request.query_params.get('product_id')
            
            if counting_id:
                # Récupérer les CountingDetail d'un comptage
                counting_details = self.counting_detail_service.get_counting_details_by_counting(int(counting_id))
                summary = self.counting_detail_service.get_counting_summary(int(counting_id))
                
                return self._create_success_response({
                    'summary': summary,
                    'counting_details': [self._serialize_counting_detail(cd) for cd in counting_details]
                })
                
            elif location_id:
                # Récupérer les CountingDetail d'un emplacement
                counting_details = self.counting_detail_service.get_counting_details_by_location(int(location_id))
                
                return self._create_success_response({
                    'location_id': location_id,
                    'counting_details': [self._serialize_counting_detail(cd) for cd in counting_details]
                })
                
            elif product_id:
                # Récupérer les CountingDetail d'un produit
                counting_details = self.counting_detail_service.get_counting_details_by_product(int(product_id))
                
                return self._create_success_response({
                    'product_id': product_id,
                    'counting_details': [self._serialize_counting_detail(cd) for cd in counting_details]
                })
                
            else:
                return self._create_error_response(
                    'Un des paramètres suivants est requis: counting_id, location_id, ou product_id'
                )
                
        except ValueError as e:
            return self._create_error_response(f'Paramètre invalide: {str(e)}')
            
        except Exception as e:
            return self._handle_exception(e)
