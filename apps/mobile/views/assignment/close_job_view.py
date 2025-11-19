from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.assignment_service import AssignmentService
from apps.mobile.serializers import CloseJobSerializer
from apps.mobile.exceptions import (
    AssignmentNotFoundException,
    InvalidStatusTransitionException,
    JobNotFoundException,
    PersonValidationException
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
        et en assignant les personnes à l'assignment.
        
        Args:
            job_id: ID du job (depuis l'URL)
            assignment_id: ID de l'assignment (depuis l'URL)
            request.data: Doit contenir {"personnes": [id1, id2]} avec min 1, max 2 personnes
        """
        try:
            # Valider les données d'entrée avec le serializer
            serializer = CloseJobSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': 'Erreur de validation',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer les IDs des personnes validés
            personnes_ids = serializer.validated_data['personnes']
            
            # Clôturer le job avec les personnes
            result = self.assignment_service.close_job(
                job_id=job_id,
                assignment_id=assignment_id,
                personnes_ids=personnes_ids
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
            
        except PersonValidationException as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Erreur interne: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
