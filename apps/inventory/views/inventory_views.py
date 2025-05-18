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
    InventoryGetByIdSerializer
)
from ..exceptions import InventoryValidationError, InventoryNotFoundError
from apps.inventory.filters import InventoryFilter
from ..repositories import InventoryRepository
from ..interfaces import IInventoryRepository

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
        Crée un nouvel inventaire.
        """
        try:
            serializer = InventoryCreateSerializer(data=request.data)
            if serializer.is_valid():
                try:
                    inventory = self.service.create_inventory(serializer.validated_data)
                    return Response({
                        "message": "Inventaire créé avec succès"
                    }, status=status.HTTP_201_CREATED)
                except InventoryValidationError as e:
                    return Response({
                        "error": str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)
            logger.warning(f"Données invalides lors de la création d'un inventaire: {serializer.errors}")
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de la création d'un inventaire: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
            serializer = InventoryGetByIdSerializer(inventory)
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