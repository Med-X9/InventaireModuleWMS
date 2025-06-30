"""
Vues pour la gestion des inventaires.
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from ..services.inventory_service import InventoryService
from ..serializers.inventory_serializer import (
    InventoryDataSerializer, 
    InventoryDetailSerializer,

)
from ..exceptions import InventoryValidationError, InventoryNotFoundError
from ..filters.inventory_filters import InventoryFilter

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
    pagination_class = StandardResultsSetPagination

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def get(self, request, *args, **kwargs):
        """
        Récupère la liste des inventaires avec filtres, tri et pagination.
        
        Paramètres de requête supportés :
        - Filtres : reference, label, status, date_gte, date_lte, etc.
        - Tri : ordering (ex: -date, label, status)
        - Pagination : page, page_size
        - Recherche : search (recherche dans label et reference)
        """
        try:
            # 1. Récupérer le queryset de base (tous les inventaires non supprimés)
            queryset = self.service.get_inventory_queryset()

            # 2. Appliquer les filtres django-filter
            filterset = InventoryFilter(request.GET, queryset=queryset)
            if not filterset.is_valid():
                return Response({
                    "success": False,
                    "errors": filterset.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            queryset = filterset.qs

            # 3. Appliquer la pagination DRF
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request, view=self)
            serializer = InventoryDetailSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des inventaires: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": "Une erreur inattendue s'est produite"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        
        """
        try:
            # 1. Validation du serializer
            serializer = InventoryDataSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Création via le service (qui utilise le use case)
            result = self.service.create_inventory(serializer.validated_data)
            
            return Response({
                "message": result.get('message', "Inventaire créé avec succès"),
                "data": result
            }, status=status.HTTP_201_CREATED)
            
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
        self.service = InventoryService()

    def get(self, request, pk, *args, **kwargs):
        """
        Récupère les détails d'un inventaire.
        """
        try:
            # Récupérer l'inventaire via le service
            inventory = self.service.get_inventory_detail(pk)
            
            # Sérialiser les données
            serializer = InventoryDetailSerializer(inventory)
            
            return Response({
                "success": True,
                "message": "Détails de l'inventaire récupérés avec succès",
                "data": serializer.data
            })
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails d'un inventaire: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": "Une erreur inattendue s'est produite"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventoryUpdateView(APIView):
    """
    Vue pour mettre à jour un inventaire.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def put(self, request, pk, *args, **kwargs):
        """
        Met à jour un inventaire.
        """
        try:
            # 1. Validation du serializer
            serializer = InventoryDataSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Mise à jour via le service (qui utilise le use case)
            result = self.service.update_inventory(pk, serializer.validated_data)
            
            return Response({
                "success": True,
                "message": result.get('message', "Inventaire mis à jour avec succès")
            }, status=status.HTTP_200_OK)
            
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de la mise à jour d'un inventaire: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de la mise à jour: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour d'un inventaire: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": "Une erreur inattendue s'est produite"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventoryDeleteView(APIView):
    """
    Vue pour effectuer un soft delete d'un inventaire.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def delete(self, request, pk, *args, **kwargs):
        """
        Supprime complètement un inventaire et tous ses enregistrements liés si son statut est en préparation.
        """
        try:
            self.service.delete_inventory(pk)
            return Response({
                "success": True,
                "message": "L'inventaire a été supprimés avec succès"
            }, status=status.HTTP_200_OK)
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de la suppression: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de la suppression: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors de la suppression d'un inventaire: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": "Une erreur inattendue s'est produite"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventorySoftDeleteView(APIView):
    """
    Vue pour effectuer un soft delete d'un inventaire.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def post(self, request, pk, *args, **kwargs):
        """
        Effectue un soft delete d'un inventaire si son statut est en préparation.
        """
        try:
            self.service.soft_delete_inventory(pk)
            return Response({
                "success": True,
                "message": "L'inventaire a été supprimés avec succès"
            }, status=status.HTTP_200_OK)
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors du supprimés: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors du supprimés: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors du supprimés d'un inventaire: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": "Une erreur inattendue s'est produite"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventoryRestoreView(APIView):
    """
    Vue pour restaurer un inventaire soft delete.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def post(self, request, pk, *args, **kwargs):
        """
        Restaure un inventaire qui a été soft delete.
        """
        try:
            print(pk)
            self.service.restore_inventory(pk)
            return Response({
                "success": True,
                "message": "L'inventaire a été restauré avec succès"
            }, status=status.HTTP_200_OK)
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de la restauration: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de la restauration: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors de la restauration d'un inventaire: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": "Une erreur inattendue s'est produite"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                "success": True,
                "message": "L'inventaire a été lancé avec succès"
            }, status=status.HTTP_200_OK)
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors du lancement: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors du lancement: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors du lancement de l'inventaire: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": "Une erreur inattendue s'est produite"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                "success": True,
                "message": "L'inventaire a été annulé avec succès"
            }, status=status.HTTP_200_OK)
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de l'annulation: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de l'annulation: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de l'inventaire: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": "Une erreur inattendue s'est produite"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InventoryTeamView(APIView):
    """
    Vue pour récupérer l'équipe d'un inventaire.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def get(self, request, pk, *args, **kwargs):
        """
        Récupère l'équipe d'un inventaire.
        """
        try:
            # Récupérer l'inventaire via le service
            inventory = self.service.get_inventory_detail(pk)
            
            # Sérialiser les données avec InventoryDetailSerializer qui inclut toutes les informations
            serializer = InventoryDetailSerializer(inventory)
            
            return Response({
                "success": True,
                "message": "Détails de l'inventaire récupérés avec succès",
                "data": serializer.data
            })

        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé: {str(e)}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails de l'inventaire: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": "Une erreur inattendue s'est produite"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 