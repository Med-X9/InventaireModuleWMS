from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from apps.mobile.services.assignment_service import AssignmentService
from apps.mobile.utils import success_response, error_response
from apps.mobile.exceptions import (
    AssignmentNotFoundException,
    UserNotAssignedException,
    AssignmentNotEntameException,
)

logger = logging.getLogger(__name__)


class BlockAssignmentView(APIView):
    """
    Vue pour bloquer un assignment.
    
    Permet de bloquer un assignment en changeant son statut vers bloqué.
    Cette opération n'est autorisée que si l'assignment est en statut ENTAME.
    
    URL: /api/mobile/assignment/{assignment_id}/block/
    
    Fonctionnalités:
    - Bloque un assignment en statut ENTAME
    - Change le statut vers bloqué
    - L'utilisateur est récupéré automatiquement depuis le token d'authentification
    - Validation des permissions utilisateur
    - Vérification que l'assignment est en statut ENTAME
    
    Paramètres d'URL:
    - assignment_id (int): ID de l'assignment à bloquer
    
    Réponses:
    - 200: Assignment bloqué avec succès
    - 400: Assignment non en statut ENTAME
    - 401: Non authentifié
    - 403: Utilisateur non autorisé pour cet assignment
    - 404: Assignment non trouvé
    - 500: Erreur interne du serveur
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.assignment_service = AssignmentService()
    
    @swagger_auto_schema(
        operation_summary="Bloquer un assignment",
        operation_description="Bloque un assignment en changeant son statut vers bloqué. Seuls les assignments en statut ENTAME peuvent être bloqués. L'utilisateur est récupéré depuis le token d'authentification",
        manual_parameters=[
            openapi.Parameter(
                'assignment_id',
                openapi.IN_PATH,
                description="ID de l'assignment à bloquer",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Assignment bloqué avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'assignment': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                        'reference': openapi.Schema(type=openapi.TYPE_STRING, example='ASS001'),
                                        'status': openapi.Schema(type=openapi.TYPE_STRING, example='bloqué'),
                                        'previous_status': openapi.Schema(type=openapi.TYPE_STRING, example='ENTAME'),
                                        'bloqued_date': openapi.Schema(type=openapi.TYPE_STRING, example='2024-01-01T10:00:00Z'),
                                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, example='2024-01-01T10:00:00Z')
                                    }
                                ),
                                'job': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                        'reference': openapi.Schema(type=openapi.TYPE_STRING, example='JOB001'),
                                        'status': openapi.Schema(type=openapi.TYPE_STRING, example='ENTAME')
                                    }
                                ),
                                'message': openapi.Schema(type=openapi.TYPE_STRING, example='Assignment ASS001 bloqué avec succès')
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Assignment non en statut ENTAME",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='L\'assignment ne peut pas être bloqué car son statut est \'TERMINE\'. Seuls les assignments en statut \'ENTAME\' peuvent être bloqués.')
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
                description="Assignment non trouvé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Assignment avec l\'ID 1 non trouvé')
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
    def post(self, request, assignment_id):
        """
        Bloque un assignment en changeant son statut vers bloqué.
        
        Args:
            request: Requête POST
            - L'utilisateur est récupéré automatiquement depuis le token d'authentification
            assignment_id: ID de l'assignment (depuis l'URL)
            
        Returns:
            Response: Confirmation de blocage avec données de l'assignment
        """
        try:
            # Récupérer l'utilisateur depuis le token d'authentification
            user_id = request.user.id
            
            # Bloquer l'assignment
            result = self.assignment_service.block_assignment(
                assignment_id, user_id
            )
            
            return success_response(
                data=result,
                message="Assignment bloqué avec succès"
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
            
        except AssignmentNotEntameException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.exception(f"Erreur lors du blocage de l'assignment {assignment_id}: {str(e)}")
            return error_response(
                message=f"Une erreur inattendue s'est produite: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
