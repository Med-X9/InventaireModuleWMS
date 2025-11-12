from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.assignment_service import AssignmentService
from apps.mobile.exceptions import (
    AssignmentNotFoundException,
    InvalidStatusTransitionException,
    JobNotFoundException
)


class CloseJobView(APIView):
    """
    Vue pour clôturer un job avec son assignment.
    Vérifie que tous les emplacements sont terminés avant de clôturer.
    
    URL: /api/mobile/job/{job_id}/close/{assignment_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.assignment_service = AssignmentService()
    
    def post(self, request, job_id, assignment_id):
        """
        Clôture un job en vérifiant que tous les emplacements sont terminés
        
        Args:
            job_id: ID du job (depuis l'URL)
            assignment_id: ID de l'assignment (depuis l'URL)
        """
        try:
            print(f"Clôture du job avec job_id={job_id} et assignment_id={assignment_id}, les données: {request.data}")
            # Clôturer le job
            result = self.assignment_service.close_job(
                job_id=job_id,
                assignment_id=assignment_id
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except JobNotFoundException as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
            
        except AssignmentNotFoundException as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
            
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
