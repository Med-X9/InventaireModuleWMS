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
    AssignmentValidationException
)


class AssignmentStatusView(APIView):
    """
    Vue pour la mise à jour des statuts d'un assignment et de son job associé.
    
    Permet de mettre à jour le statut d'un assignment et de son job correspondant
    vers le statut "ENTAME" dans l'application mobile. Gère la cohérence des
    statuts entre les deux entités.
    
    URL: /api/mobile/user/{user_id}/assignment/{assignment_id}/status/
    
    Fonctionnalités:
    - Mise à jour du statut assignment vers ENTAME
    - Mise à jour du statut job associé vers ENTAME
    - Validation des permissions utilisateur
    - Gestion des transitions de statut valides
    - Cohérence des données entre assignment et job
    
    Paramètres d'URL:
    - user_id (int): ID de l'utilisateur assigné
    - assignment_id (int): ID de l'assignment à mettre à jour
    
    Réponses:
    - 200: Statut mis à jour avec succès
    - 400: Transition de statut invalide
    - 401: Non authentifié
    - 403: Utilisateur non autorisé pour cet assignment
    - 404: Assignment ou job non trouvé
    - 500: Erreur interne du serveur
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.assignment_service = AssignmentService()
    
    def post(self, request, user_id, assignment_id):
        """
        Met à jour le statut d'un assignment et de son job vers ENTAME.
        
        Args:
            request: Requête POST
            user_id: ID de l'utilisateur (depuis l'URL)
            assignment_id: ID de l'assignment (depuis l'URL)
            
        Returns:
            Response: Confirmation de mise à jour avec données des statuts
        """
        try:
            # Statut fixe : ENTAME
            new_status = "ENTAME"
            
            # Mettre à jour les deux statuts
            result = self.assignment_service.update_assignment_and_job_status(
                assignment_id, user_id, new_status
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
