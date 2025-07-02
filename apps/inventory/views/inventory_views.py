"""
Vues pour la gestion des inventaires.
"""
import logging
from rest_framework import status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Inventory
from ..services.inventory_service import InventoryService
from ..serializers.inventory_serializer import (
    InventoryCreateSerializer, 
    InventoryDetailSerializer,
    InventoryGetByIdSerializer,
    InventoryTeamSerializer,
    InventoryWarehouseStatsSerializer
)
from ..exceptions import InventoryValidationError, InventoryNotFoundError
from ..filters import InventoryFilter
from ..repositories import InventoryRepository
from ..interfaces import IInventoryRepository
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

# Configuration du logger
logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class InventoryListView(APIView):
    """
    Vue pour lister les inventaires avec pagination et filtres.
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = InventoryFilter
    search_fields = ['label', 'reference']
    ordering_fields = ['date', 'label', 'status']
    ordering = '-date'  # Tri par défaut par date décroissante
    pagination_class = StandardResultsSetPagination

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository = InventoryRepository()

    def get(self, request, *args, **kwargs):
        """
        Récupère la liste des inventaires avec filtres et pagination.
        """
        try:
            # Récupérer les paramètres de filtrage
            filters_dict = request.query_params.dict()
            
            # Récupérer le queryset filtré via le repository
            queryset = self.repository.get_by_filters(filters_dict)

            # Appliquer le tri
            ordering = request.query_params.get('ordering', self.ordering)
            if ordering:
                if ordering.startswith('-'):
                    field = ordering[1:]
                    queryset = queryset.order_by(f'-{field}')
                else:
                    queryset = queryset.order_by(ordering)

            # Appliquer la pagination
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request)

            # Sérialiser les résultats
            serializer = InventoryDetailSerializer(page, many=True)

            # Retourner la réponse paginée avec un message de succès
            response = paginator.get_paginated_response(serializer.data)
            response.data['message'] = "Liste des inventaires récupérée avec succès"
            return response

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des inventaires: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class InventoryCreateView(APIView):
    """
    Vue pour créer un nouvel inventaire.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def post(self, request, *args, **kwargs):
        """
        Crée un nouvel inventaire avec validation complète.
        
        Format JSON attendu:
        {
            "label": "Inventaire trimestriel Q1 2023",
            "date": "2024-03-20",
            "account_id": 2,
            "warehouse": [
                {"id": 1, "date": "12/12/2025"},
                {"id": 2, "date": "12/12/2025"}
            ],
            "comptages": [
                {
                    "order": 1,
                    "count_mode": "en vrac",
                    "unit_scanned": true,
                    "entry_quantity": false,
                    "is_variant": false,
                    "stock_situation": false,
                    "quantity_show": true,
                    "show_product": true,
                    "dlc": false,
                    "n_serie": false,
                    "n_lot": false
                }
            ]
        }
        """
        try:
            # 1. Validation du serializer
            serializer = InventoryCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Création via le service (qui utilise maintenant le use case)
            result = self.service.create_inventory(serializer.validated_data)
            
            return Response(result, status=status.HTTP_201_CREATED)
            
        except InventoryValidationError as e:
            logger.error(f"Erreur de validation: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur inattendue: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Une erreur inattendue s\'est produite'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventoryDetailView(APIView):
    """
    Vue pour récupérer les détails d'un inventaire.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository = InventoryRepository()

    def get(self, request, pk, *args, **kwargs):
        """
        Récupère les détails d'un inventaire.
        """
        try:
            inventory = self.repository.get_with_related_data(pk)
            serializer = InventoryDetailSerializer(inventory)
            return Response({
                "message": "Détails de l'inventaire récupérés avec succès",
                "data": serializer.data
            })
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails d'un inventaire: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class InventoryUpdateView(APIView):
    """
    Vue pour mettre à jour un inventaire.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository = InventoryRepository()

    def put(self, request, pk, *args, **kwargs):
        """
        Met à jour un inventaire.
        """
        try:
            serializer = InventoryCreateSerializer(data=request.data)
            if serializer.is_valid():
                inventory = self.repository.update(pk, serializer.validated_data)
                return Response({
                    "message": "Inventaire mis à jour avec succès"
                   
                }, status=status.HTTP_200_OK)
            logger.warning(f"Données invalides lors de la mise à jour d'un inventaire: {serializer.errors}")
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de la mise à jour: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour d'un inventaire: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class InventoryDeleteView(APIView):
    """
    Vue pour effectuer un soft delete d'un inventaire.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository = InventoryRepository()

    def delete(self, request, pk, *args, **kwargs):
        """
        Effectue un soft delete d'un inventaire si son statut est en attente.
        """
        try:
            service = InventoryService()
            service.delete_inventory(pk)
            return Response({
                "message": "L'inventaire a été supprimé avec succès"
            }, status=status.HTTP_200_OK)
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de la suppression: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de la suppression: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors de la suppression d'un inventaire: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventoryLaunchView(APIView):
    """
    Vue pour lancer un inventaire.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def post(self, request, pk, *args, **kwargs):
        """
        Lance un inventaire en vérifiant le mode de comptage et en remplissant les détails si nécessaire.
        """
        try:
            self.service.launch_inventory(pk)
            return Response({
                "message": "L'inventaire a été lancé avec succès"
            }, status=status.HTTP_200_OK)
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors du lancement: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors du lancement: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors du lancement de l'inventaire: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventoryCancelView(APIView):
    """
    Vue pour annuler le lancement d'un inventaire.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def post(self, request, pk, *args, **kwargs):
        """
        Annule le lancement d'un inventaire.
        """
        try:
            self.service.cancel_inventory(pk)
            return Response({
                "message": "L'inventaire a été annulé avec succès"
            }, status=status.HTTP_200_OK)
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de l'annulation: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de l'annulation: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de l'inventaire: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventoryTeamView(APIView):
    """
    Vue pour récupérer l'équipe d'un inventaire.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository = InventoryRepository()

    def get(self, request, pk, *args, **kwargs):
        """
        Récupère l'équipe d'un inventaire.
        """
        try:
            # Vérifier si l'inventaire existe et récupérer toutes les données associées
            inventory = self.repository.get_with_related_data(pk)
            
            # Sérialiser les données avec InventoryDetailSerializer qui inclut toutes les informations
            serializer = InventoryDetailSerializer(inventory)
            
            return Response({
                "message": "Détails de l'inventaire récupérés avec succès",
                "data": serializer.data
            })

        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails de l'inventaire: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class InventoryWarehouseStatsView(APIView):
    """
    Vue pour récupérer les statistiques des warehouses d'un inventaire.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, inventory_id):
        """
        Récupère les statistiques des warehouses pour un inventaire.
        
        Args:
            request: La requête HTTP
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Response: La réponse HTTP avec les statistiques des warehouses
        """
        try:
            # Récupérer les statistiques via le service
            inventory_service = InventoryService()
            stats_data = inventory_service.get_warehouse_stats_for_inventory(inventory_id)
            
            # Sérialiser les données
            serializer = InventoryWarehouseStatsSerializer(stats_data, many=True)
            
            return Response({
                'status': 'success',
                'message': 'Statistiques des warehouses récupérées avec succès',
                'inventory_id': inventory_id,
                'warehouses_count': len(stats_data),
                'data': serializer.data
            })
            
        except InventoryNotFoundError as e:
            return Response({
                'status': 'error',
                'message': 'Inventaire non trouvé',
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
            
        except InventoryValidationError as e:
            return Response({
                'status': 'error',
                'message': 'Erreur de validation',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques des warehouses: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Erreur lors de la récupération des statistiques des warehouses',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 