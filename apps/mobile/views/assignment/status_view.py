from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.assignment_service import AssignmentService
from apps.mobile.exceptions import (
    AssignmentNotFoundException,
    UserNotAssignedException,
    InvalidStatusTransitionException,
    JobNotFoundException,
    AssignmentValidationException,
    AssignmentAlreadyStartedException
)


class AssignmentStatusView(APIView):
    """
    Vue pour la mise à jour des statuts d'un assignment et de son job
    URL: /api/mobile/user/{user_id}/job/{job_id}/status/
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.assignment_service = AssignmentService()
    
    def post(self, request, user_id, job_id):
        """
        Met à jour le statut d'un assignment et de son job vers ENTAME
        
        Args:
            user_id: ID de l'utilisateur (depuis l'URL)
            job_id: ID du job (depuis l'URL)
            Pas besoin de body - le statut est automatiquement ENTAME
        """
        try:
            # Statut fixe : ENTAME
            new_status = "ENTAME"
            
            # Mettre à jour les deux statuts
            result = self.assignment_service.update_assignment_and_job_status_by_job_id(
                job_id, user_id, new_status
            )
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
            
        except AssignmentNotFoundException as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
            
        except UserNotAssignedException as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
            
        except JobNotFoundException as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
            
        except AssignmentAlreadyStartedException as e:
            return Response({
                'success': False,
                'error': str(e),
                'message': "L'assignment est déjà entamé et ne peut pas être modifié"
            }, status=status.HTTP_409_CONFLICT)
            
        except InvalidStatusTransitionException as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Erreur interne: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
