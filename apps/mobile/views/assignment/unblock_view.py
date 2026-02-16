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
    AssignmentNotBloqueException,
    MaxEntameAssignmentsException,
)

logger = logging.getLogger(__name__)


class UnblockAssignmentView(APIView):
    """
    Vue pour débloquer un assignment.
    
    Permet de débloquer un assignment en changeant son statut vers ENTAME.
    Cette opération n'est autorisée que si l'assignment est en statut bloqué.
    Vérifie également qu'il n'y a pas déjà 3 assignments ENTAME pour le même utilisateur et inventory.
    
    URL: /api/mobile/assignment/{assignment_id}/unblock/
    
    Fonctionnalités:
    - Débloque un assignment en statut bloqué
    - Change le statut vers ENTAME
    - L'utilisateur est récupéré automatiquement depuis le token d'authentification
    - Validation des permissions utilisateur
    - Vérification que l'assignment est en statut bloqué
    - Vérification qu'il n'y a pas déjà 3 assignments ENTAME pour le même inventory
    
    Paramètres d'URL:
    - assignment_id (int): ID de l'assignment à débloquer
    
    Réponses:
    - 200: Assignment débloqué avec succès
    - 400: Assignment non en statut bloqué ou maximum d'assignments ENTAME atteint
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
        operation_summary="Débloquer un assignment",
        operation_description="Débloque un assignment en changeant son statut vers ENTAME. Seuls les assignments en statut bloqué peuvent être débloqués. Vérifie également qu'il n'y a pas déjà 3 assignments ENTAME pour le même inventory. L'utilisateur est récupéré depuis le token d'authentification",
        manual_parameters=[
            openapi.Parameter(
                'assignment_id',
                openapi.IN_PATH,
                description="ID de l'assignment à débloquer",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Assignment débloqué avec succès",
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
                                        'status': openapi.Schema(type=openapi.TYPE_STRING, example='ENTAME'),
                                        'previous_status': openapi.Schema(type=openapi.TYPE_STRING, example='bloqué'),
                                        'debloqued_date': openapi.Schema(type=openapi.TYPE_STRING, example='2024-01-01T10:00:00Z'),
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
                                'message': openapi.Schema(type=openapi.TYPE_STRING, example='Assignment ASS001 débloqué avec succès')
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Assignment non en statut bloqué ou maximum d'assignments ENTAME atteint",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            example='Vous ne pouvez pas débloquer cet assignment car vous avez déjà 3 assignments en statut ENTAME pour le même inventaire. Pour débloquer, vous devez terminer ou bloquer un assignment.'
                        )
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
        Débloque un assignment en changeant son statut vers ENTAME.
        
        Args:
            request: Requête POST
            - L'utilisateur est récupéré automatiquement depuis le token d'authentification
            assignment_id: ID de l'assignment (depuis l'URL)
            
        Returns:
            Response: Confirmation de déblocage avec données de l'assignment
        """
        try:
            # Récupérer l'utilisateur depuis le token d'authentification
            user_id = request.user.id
            
            # Débloquer l'assignment
            result = self.assignment_service.unblock_assignment(
                assignment_id, user_id
            )
            
            return success_response(
                data=result,
                message="Assignment débloqué avec succès"
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
            
        except AssignmentNotBloqueException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except MaxEntameAssignmentsException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.exception(f"Erreur lors du déblocage de l'assignment {assignment_id}: {str(e)}")
            return error_response(
                message=f"Une erreur inattendue s'est produite: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
