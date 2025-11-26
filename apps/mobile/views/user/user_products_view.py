from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.mobile.services.user_service import UserService
from apps.mobile.utils import success_response, error_response
from apps.mobile.exceptions import (
    UserNotFoundException,
    AccountNotFoundException,
    ProductNotFoundException,
    DataValidationException,
    DatabaseConnectionException
)


class UserProductsView(APIView):
    """
    API pour récupérer les produits du même compte qu'un utilisateur.
    
    Permet de récupérer la liste des produits appartenant au même compte
    de l'utilisateur connecté. Utile pour la gestion des inventaires
    et l'affichage des produits disponibles pour le comptage.
    
    URL: /mobile/api/products/
    
    Fonctionnalités:
    - Récupération des produits du même compte
    - L'utilisateur est récupéré automatiquement depuis le token d'authentification
    - Filtrage par compte associé à l'utilisateur connecté
    - Gestion des erreurs spécifiques et cas d'absence de produits
    
    Réponses:
    - 200: Liste des produits récupérée avec succès (peut être vide)
    - 400: Erreur de validation
    - 401: Non authentifié
    - 404: Utilisateur ou compte non trouvé
    - 500: Erreur interne du serveur ou erreur de base de données
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Récupération des produits utilisateur mobile",
        operation_description="Récupère la liste des produits appartenant au même compte de l'utilisateur connecté (récupéré depuis le token)",
        responses={
            200: openapi.Response(
                description="Liste des produits récupérée avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Produits récupérés avec succès'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'products': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'web_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=5105),
                                            'product_name': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, example=None),
                                            'product_code': openapi.Schema(type=openapi.TYPE_STRING, example='8690644022340'),
                                            'internal_product_code': openapi.Schema(type=openapi.TYPE_STRING, example='M0405-0001'),
                                            'family_name': openapi.Schema(type=openapi.TYPE_STRING, example='PASTEL'),
                                            'is_variant': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                                            'n_lot': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                                            'n_serie': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                                            'dlc': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                                            'numeros_serie': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), example=[]),
                                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
                                        }
                                    ),
                                    description="Liste des produits du même compte"
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Erreur de validation",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Erreur de validation'),
                        'error_type': openapi.Schema(type=openapi.TYPE_STRING, example='VALIDATION_ERROR')
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
                description="Utilisateur ou compte non trouvé",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Utilisateur non trouvé'),
                        'error_type': openapi.Schema(type=openapi.TYPE_STRING, example='USER_NOT_FOUND')
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
        tags=['Utilisateur Mobile']
    )
    def get(self, request):
        """
        Récupère les produits du même compte de l'utilisateur connecté.
        
        Args:
            request: Requête GET
            - L'utilisateur est récupéré automatiquement depuis le token d'authentification
            
        Returns:
            Response: Liste des produits avec seulement les informations essentielles
        """
        try:
            # Récupérer l'utilisateur depuis le token d'authentification
            user_id = request.user.id
            print(f"user_id depuis token: {user_id}")
            
            user_service = UserService()
            
            response_data = user_service.get_user_products(user_id)
            
            # Extraire seulement les informations demandées de chaque produit
            products = []
            if response_data and 'data' in response_data and 'products' in response_data['data']:
                for product in response_data['data']['products']:
                    products.append({
                        'web_id': product.get('web_id'),
                        'product_name': product.get('product_name'),
                        'product_code': product.get('product_code'),
                        'internal_product_code': product.get('internal_product_code'),
                        'family_name': product.get('family_name'),
                        'is_variant': product.get('is_variant'),
                        'n_lot': product.get('n_lot'),
                        'n_serie': product.get('n_serie'),
                        'dlc': product.get('dlc'),
                        'numeros_serie': product.get('numeros_serie', []),
                        'created_at': product.get('created_at'),
                        'updated_at': product.get('updated_at')
                    })
            
            # Retourner avec success_response mais seulement les products dans data
            return success_response(
                data={'products': products},
                message="Produits récupérés avec succès"
            )
            
        except UserNotFoundException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
                error_type='USER_NOT_FOUND'
            )
        except AccountNotFoundException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
                error_type='ACCOUNT_NOT_FOUND'
            )
        except ProductNotFoundException as e:
            return success_response(
                data={'products': []},
                message="Produits récupérés avec succès"
            )
        except DataValidationException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='VALIDATION_ERROR'
            )
        except DatabaseConnectionException as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_type='DATABASE_ERROR'
            )
        except ValueError as e:
            return error_response(
                message=f'Erreur de validation: {str(e)}',
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type='VALIDATION_ERROR'
            )
        except Exception as e:
            print(f"Erreur inattendue dans UserProductsView: {str(e)}")
            import traceback
            print(f"Traceback complet: {traceback.format_exc()}")
            return error_response(
                message="Erreur interne du serveur",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_type='INTERNAL_ERROR'
            )
