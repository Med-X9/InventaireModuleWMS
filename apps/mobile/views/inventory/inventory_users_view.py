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
    Liste des inventaires EN REALISATION de l'utilisateur connecté,
    avec uniquement les magasins où il est affecté (Assigment.session).

    URL: GET /mobile/api/inventory/
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Inventaires EN REALISATION pour l'utilisateur (magasins affectés uniquement)",
        operation_description=(
            "Retourne les inventaires EN REALISATION liés aux affectations de "
            "l'utilisateur authentifié. La liste warehouses ne contient que les "
            "magasins où la session est réellement affectée."
        ),
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
                                            'warehouses': openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                items=openapi.Schema(
                                                    type=openapi.TYPE_OBJECT,
                                                    properties={
                                                        'web_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                                        'reference': openapi.Schema(type=openapi.TYPE_STRING, example='WH-001'),
                                                        'warehouse_name': openapi.Schema(type=openapi.TYPE_STRING, example='Entrepôt Central'),
                                                        'warehouse_type': openapi.Schema(type=openapi.TYPE_STRING, example='CENTRAL'),
                                                        'status': openapi.Schema(type=openapi.TYPE_STRING, example='ACTIVE'),
                                                        'description': openapi.Schema(type=openapi.TYPE_STRING, example='Entrepôt principal'),
                                                        'address': openapi.Schema(type=openapi.TYPE_STRING, example='123 Rue Example'),
                                                    }
                                                ),
                                                description="Magasins où l'utilisateur est affecté uniquement"
                                            ),
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
        Inventaires EN REALISATION + magasins d'affectation de l'utilisateur connecté.
        """
        try:
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
