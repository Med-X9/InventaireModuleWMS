from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.mobile.services.assignment_service import AssignmentService
from apps.mobile.utils import success_response, error_response
from apps.mobile.exceptions import (
    AssignmentNotFoundException,
    UserNotAssignedException,
    InvalidStatusTransitionException,
    JobNotFoundException,
    AssignmentAlreadyStartedException,
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
    
    @swagger_auto_schema(
        operation_summary="Mise à jour du statut d'assignment mobile",
        operation_description="Met à jour le statut d'un assignment et de son job associé vers ENTAME",
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description="ID de l'utilisateur assigné",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'assignment_id',
                openapi.IN_PATH,
                description="ID de l'assignment à mettre à jour",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Statut mis à jour avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'assignment_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                'job_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                'new_status': openapi.Schema(type=openapi.TYPE_STRING, example='ENTAME'),
                                'updated_at': openapi.Schema(type=openapi.TYPE_STRING, example='2024-01-01T10:00:00Z')
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Transition de statut invalide ou assignment déjà entamé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Transition de statut invalide ou assignment déjà entamé')
                    }
                )
            ),
            401: openapi.Response(
                description="Non authentifié",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example='Authentication credentials were not provided.')
                    }
                )
            ),
            403: openapi.Response(
                description="Utilisateur non autorisé pour cet assignment",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Utilisateur non autorisé pour cet assignment')
                    }
                )
            ),
            404: openapi.Response(
                description="Assignment ou job non trouvé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Assignment non trouvé')
                    }
                )
            ),
            500: openapi.Response(
                description="Erreur interne du serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Erreur interne du serveur')
                    }
                )
            )
        },
        security=[{'Bearer': []}],
        tags=['Assignment Mobile']
    )
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
            
            return success_response(
                data=result,
                message="Statut mis à jour avec succès"
            )
            
        except AssignmentNotFoundException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        except UserNotAssignedException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        except JobNotFoundException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        except InvalidStatusTransitionException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except AssignmentAlreadyStartedException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return error_response(
                message="Une erreur inattendue s'est produite",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
