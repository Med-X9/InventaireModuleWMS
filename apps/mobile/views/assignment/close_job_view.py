from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.assignment_service import AssignmentService
from apps.mobile.serializers import CloseJobSerializer
from apps.mobile.utils import success_response, error_response, validation_error_response
from apps.mobile.exceptions import (
    AssignmentNotFoundException,
    InvalidStatusTransitionException,
    JobNotFoundException,
    PersonValidationException
)


class CloseJobView(APIView):
    """
    Vue pour clôturer un assignment et potentiellement le job associé.
    
    Cette API :
    1. Marque l'assignment comme TERMINE
    2. Vérifie si TOUS les assignments du job sont TERMINE
    3. Vérifie si tous les EcartComptage de l'inventaire ont un final_result non null
    4. Si les deux conditions précédentes sont remplies, marque le job comme TERMINE
    
    URL: /api/mobile/job/{job_id}/close/{assignment_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.assignment_service = AssignmentService()
    
    def post(self, request, job_id, assignment_id):
        """
        Clôture un assignment et vérifie si le job peut être clôturé.
        
        Args:
            job_id: ID du job (depuis l'URL)
            assignment_id: ID de l'assignment (depuis l'URL)
            request.data: Doit contenir {"personnes": [id1, id2]} avec min 1, max 2 personnes
            
        Returns:
            Response avec les informations de clôture incluant :
            - Le statut de l'assignment (toujours TERMINE)
            - Le statut du job (TERMINE si toutes les conditions sont remplies)
            - Les informations sur les conditions de clôture du job
        """
        try:
            # Valider les données d'entrée avec le serializer
            serializer = CloseJobSerializer(data=request.data)
            if not serializer.is_valid():
                return validation_error_response(
                    serializer.errors,
                    message="Erreur de validation lors de la clôture du job"
                )
            
            # Récupérer les IDs des personnes validés
            personnes_ids = serializer.validated_data['personnes']
            
            # Clôturer l'assignment et vérifier si le job peut être clôturé
            result = self.assignment_service.close_job(
                job_id=job_id,
                assignment_id=assignment_id,
                personnes_ids=personnes_ids
            )
            
            # Message adapté selon si le job a été clôturé ou non
            if result.get('job_closure_status', {}).get('job_closed', False):
                message = "Assignment et job clôturés avec succès"
            else:
                message = "Assignment clôturé avec succès. Le job sera clôturé lorsque tous les assignments seront terminés et tous les écarts auront un résultat final."
            
            return success_response(
                data=result,
                message=message
            )
            
        except JobNotFoundException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        except AssignmentNotFoundException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        except InvalidStatusTransitionException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except PersonValidationException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return error_response(
                message="Une erreur inattendue s'est produite lors de la clôture du job",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
