from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.mobile.services.sync_service import SyncService
from apps.mobile.exceptions import UploadDataException


class UploadDataView(APIView):
    """
    API d'upload unifiée pour l'application mobile.
    
    Traite tous les types d'uploads en une seule requête pour optimiser
    les performances et réduire la complexité côté client mobile.
    
    Fonctionnalités:
    - Upload des données de comptage (CountingDetail)
    - Upload des données d'assignment
    - Validation et traitement en lot
    - Gestion des conflits de données
    - Synchronisation avec le serveur
    
    Paramètres de requête:
    - sync_id (string): Identifiant de synchronisation
    - countings (array): Données de comptage à uploader
    - assignments (array): Données d'assignment à uploader
    
    Réponses:
    - 200: Upload réussi avec résumé des opérations
    - 400: Données invalides ou erreur de validation
    - 401: Non authentifié
    - 500: Erreur interne du serveur
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Upload des données mobile",
        operation_description="Traite tous les types d'uploads en une seule requête pour optimiser les performances et réduire la complexité côté client mobile",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['sync_id'],
            properties={
                'sync_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Identifiant de synchronisation',
                    example='sync_123456789'
                ),
                'countings': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT),
                    description='Données de comptage à uploader',
                    example=[
                        {
                            'counting_id': 1,
                            'product_id': 1,
                            'location_id': 1,
                            'quantity': 10,
                            'status': 'COMPLETED'
                        }
                    ]
                ),
                'assignments': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT),
                    description='Données d\'assignment à uploader',
                    example=[
                        {
                            'assignment_id': 1,
                            'status': 'COMPLETED',
                            'completion_date': '2024-01-01T10:00:00Z'
                        }
                    ]
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Upload réussi avec résumé des opérations",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Upload réussi'),
                        'countings_processed': openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
                        'assignments_processed': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                        'errors': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            description="Liste des erreurs rencontrées"
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Données invalides ou erreur de validation",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Données invalides')
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
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Erreur interne du serveur')
                    }
                )
            )
        },
        security=[{'Bearer': []}],
        tags=['Synchronisation Mobile']
    )
    def post(self, request):
        try:
            sync_service = SyncService()
            
            # sync_id = request.data.get('sync_id')
            # if not sync_id:
            #     return Response({
            #         'success': False,
            #         'error': 'sync_id requis'
            #     }, status=status.HTTP_400_BAD_REQUEST)
            
            countings = request.data.get('countings', [])
            assignments = request.data.get('assignments', [])
            
            response_data = sync_service.upload_data( countings, assignments)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': f'Données invalides: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except UploadDataException as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Erreur inattendue dans UploadDataView: {str(e)}")
            return Response({
                'success': False,
                'error': 'Erreur interne du serveur'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
