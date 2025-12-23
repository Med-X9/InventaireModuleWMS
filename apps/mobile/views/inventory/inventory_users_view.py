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
    API pour récupérer la liste des inventaires avec statut EN REALISATION
    affectés à l'utilisateur authentifié.
    
    Permet de récupérer la liste des inventaires en cours de réalisation
    pour lesquels l'utilisateur authentifié a des assignments actifs.
    Utile pour l'affichage des inventaires disponibles dans l'application mobile.
    
    URL: /mobile/api/inventory/
    
    Fonctionnalités:
    - Récupération des inventaires EN REALISATION
    - Filtrage par assignments de l'utilisateur authentifié
    - Retourne uniquement les inventaires avec des jobs TRANSFERT ou ENTAME
    - Gestion des erreurs spécifiques
    
    Réponses:
    - 200: Liste des inventaires récupérée avec succès
    - 401: Non authentifié
    - 500: Erreur interne du serveur
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Récupération des inventaires EN REALISATION pour l'utilisateur mobile",
        operation_description="Récupère la liste des inventaires avec statut EN REALISATION affectés à l'utilisateur authentifié",
        responses={
            200: openapi.Response(
                description="Liste des inventaires récupérée avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'inventories': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'web_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                            'reference': openapi.Schema(type=openapi.TYPE_STRING, example='INV-123'),
                                            'label': openapi.Schema(type=openapi.TYPE_STRING, example='Inventaire principal'),
                                            'status': openapi.Schema(type=openapi.TYPE_STRING, example='EN REALISATION'),
                                            'inventory_type': openapi.Schema(type=openapi.TYPE_STRING, example='GENERAL'),
                                            'date': openapi.Schema(type=openapi.TYPE_STRING, example='2025-01-15T10:00:00Z'),
                                            'en_realisation_status_date': openapi.Schema(type=openapi.TYPE_STRING, example='2025-01-15T10:00:00Z'),
                                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, example='2025-01-15T10:00:00Z'),
                                            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, example='2025-01-15T10:00:00Z'),
                                        }
                                    ),
                                    description="Liste des inventaires EN REALISATION"
                                )
                            }
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
    def get(self, request):
        """
        Récupère la liste des inventaires EN REALISATION affectés à l'utilisateur authentifié.
        
        Args:
            request: Requête GET
            - L'utilisateur est récupéré automatiquement depuis le token d'authentification
            
        Returns:
            Response: Liste des inventaires EN REALISATION
        """
        try:
            # Récupérer l'utilisateur depuis le token d'authentification
            user_id = request.user.id
            
            inventory_service = InventoryService()
            
            response_data = inventory_service.get_user_inventories(user_id)
            
            return success_response(
                data=response_data,
                message="Inventaires récupérés avec succès"
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
