from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.mobile.services.inventory_service import InventoryService
from apps.mobile.utils import success_response, error_response
from apps.mobile.exceptions import (
    InventoryNotFoundException,
    AccountNotFoundException
)


class InventoryUsersView(APIView):
    """
    API pour récupérer les utilisateurs du même compte qu'un inventaire.
    
    Permet de récupérer la liste des utilisateurs appartenant au même compte
    qu'un inventaire spécifique. Utile pour la gestion des équipes d'inventaire
    et l'affichage des utilisateurs disponibles pour les assignments.
    
    URL: /mobile/api/inventory/{inventory_id}/users/
    
    Fonctionnalités:
    - Récupération des utilisateurs du même compte
    - Validation de l'existence de l'inventaire
    - Filtrage par compte associé à l'inventaire
    - Gestion des erreurs spécifiques
    
    Paramètres d'URL:
    - inventory_id (int): ID de l'inventaire
    
    Réponses:
    - 200: Liste des utilisateurs récupérée avec succès
    - 400: ID d'inventaire invalide
    - 401: Non authentifié
    - 404: Inventaire ou compte non trouvé
    - 500: Erreur interne du serveur
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Récupération des utilisateurs d'inventaire mobile",
        operation_description="Récupère la liste des utilisateurs appartenant au même compte qu'un inventaire spécifique",
        manual_parameters=[
            openapi.Parameter(
                'inventory_id',
                openapi.IN_PATH,
                description="ID de l'inventaire",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Liste des utilisateurs récupérée avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'users': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_OBJECT),
                                    description="Liste des utilisateurs du même compte"
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="ID d'inventaire invalide",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='ID d\'inventaire invalide'),
                        'error_type': openapi.Schema(type=openapi.TYPE_STRING, example='INVALID_PARAMETER')
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
            404: openapi.Response(
                description="Inventaire ou compte non trouvé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Inventaire non trouvé'),
                        'error_type': openapi.Schema(type=openapi.TYPE_STRING, example='INVENTORY_NOT_FOUND')
                    }
                )
            ),
            500: openapi.Response(
                description="Erreur interne du serveur",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Erreur interne du serveur'),
                        'error_type': openapi.Schema(type=openapi.TYPE_STRING, example='INTERNAL_ERROR')
                    }
                )
            )
        },
        security=[{'Bearer': []}],
        tags=['Inventaire Mobile']
    )
    def get(self, request, inventory_id):
        """
        Récupère les utilisateurs du même compte qu'un inventaire.
        
        Args:
            request: Requête GET
            inventory_id: ID de l'inventaire (depuis l'URL)
            
        Returns:
            Response: Liste des utilisateurs du même compte que l'inventaire
        """
        try:
            inventory_service = InventoryService()
            
            response_data = inventory_service.get_inventory_users(inventory_id)
            
            return success_response(
                data=response_data,
                message="Utilisateurs récupérés avec succès"
            )
            
        except InventoryNotFoundException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
                error_type='INVENTORY_NOT_FOUND'
            )
        except AccountNotFoundException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
                error_type='ACCOUNT_NOT_FOUND'
            )
        except ValueError as e:
            return error_response(
                message=f'ID d\'inventaire invalide: {str(e)}',
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='INVALID_PARAMETER'
            )
        except Exception as e:
            print(f"Erreur inattendue dans InventoryUsersView: {str(e)}")
            import traceback
            print(f"Traceback complet: {traceback.format_exc()}")
            return error_response(
                message="Erreur interne du serveur",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_type='INTERNAL_ERROR'
            )
