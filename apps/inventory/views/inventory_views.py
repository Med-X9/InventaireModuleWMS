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
from ..services.inventory_result_service import InventoryResultService
from ..services.inventory_service import InventoryService
from ..serializers.inventory_serializer import (
    InventoryCreateSerializer,
    InventoryDuplicateSerializer,
    InventoryDetailSerializer,
    InventoryGetByIdSerializer,
    InventoryTeamSerializer,
    InventoryWarehouseStatsSerializer,
    InventoryUpdateSerializer,
    InventoryDetailModeFieldsSerializer,
    InventoryDetailWithWarehouseSerializer,
)
from ..serializers import InventoryWarehouseResultSerializer
from ..exceptions import InventoryValidationError, InventoryNotFoundError, StockValidationError
from ..filters import InventoryFilter
from ..repositories import InventoryRepository
from ..interfaces import IInventoryRepository
from ..utils.response_utils import success_response, error_response, validation_error_response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from apps.inventory.usecases.inventory_launch_validation import InventoryLaunchValidationUseCase
from apps.core.datatables.mixins import ServerSideDataTableView, quick_datatable_view
from apps.core.datatables.base import DataTableConfig, IDataTableFilter
from apps.core.datatables.filters import (
    DjangoFilterDataTableFilter, DateRangeFilter, StatusFilter, CompositeDataTableFilter,
    StringFilter, DateFilter, NumberFilter, FilterMappingFilter
)
from apps.core.datatables.serializers import DataTableSerializer

# Configuration du logger
logger = logging.getLogger(__name__)


class InventoryListView(ServerSideDataTableView):
    """
    Vue pour lister les inventaires avec pagination et filtres.
    Supporte à la fois l'API REST normale et DataTable ServerSide.
    
    FONCTIONNALITÉS AUTOMATIQUES:
    - Tri sur tous les champs configurés (ordering=field ou -field)
    - Tri DataTable (order[0][column]=index&order[0][dir]=asc/desc)
    - Recherche sur champs multiples
    - Filtrage avancé avec django-filter
    - Filtrage par date (date_exact, date_start, date_end)
    - Filtrage par statut (status, status_in)
    - Pagination optimisée
    - Sérialisation flexible
    
    PARAMÈTRES DE REQUÊTE SUPPORTÉS:
    - Tri: ordering=label, ordering=-date, ordering=created_at, ordering=reference, ordering=status, ordering=inventory_type
    - Tri DataTable: order[0][column]=2&order[0][dir]=asc
    - Recherche: search=terme
    - Pagination: page=1&page_size=25
    - Filtres: status=active, inventory_type=general, reference=INV-xxx
    - Dates: date_exact=2024-01-01, date_start=2024-01-01, date_end=2024-12-31
    - Statuts: status=active, status_in=active,pending,completed
    """
    
    # Configuration de base
    model = Inventory
    serializer_class = InventoryDetailSerializer
    
    # Champs de recherche et tri - TOUS LES CHAMPS
    search_fields = [
        'label', 'reference', 'status', 'inventory_type', 
        'account_name', 'warehouse_name', 'created_at', 'date',
        'en_preparation_status_date', 'en_realisation_status_date', 
        'termine_status_date', 'cloture_status_date'
    ]
    order_fields = [
        'id', 'reference', 'label', 'date', 'status', 'inventory_type', 
        'created_at', 'updated_at', 'en_preparation_status_date', 
        'en_realisation_status_date', 'termine_status_date', 'cloture_status_date'
    ]
    default_order = '-created_at'
    
    # Configuration de pagination
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    
    # Champs de filtrage automatique - TOUS LES CHAMPS
    filter_fields = [
        'status', 'inventory_type', 'reference', 'label', 'id',
        'label_contains', 'label_exact', 'label_startswith', 'label_endswith',
        'reference_contains', 'reference_exact',
        'account_contains', 'warehouse_contains',
        'count_mode_contains'
    ]
    date_fields = [
        'date', 'created_at', 'updated_at', 'en_preparation_status_date', 
        'en_realisation_status_date', 'termine_status_date', 'cloture_status_date'
    ]
    status_fields = ['status']
    
    # Mapping frontend -> backend aligné sur les colonnes du DataTable
    # Les clés correspondent aux champs utilisés côté frontend (InventoryManagement.vue)
    filter_aliases = {
        # Colonnes principales visibles
        'label': 'label',
        'date': 'date',
        'status': 'status',
        'en_preparation_status_date': 'en_preparation_status_date',
        'en_realisation_status_date': 'en_realisation_status_date',
        'termine_status_date': 'termine_status_date',
        'cloture_status_date': 'cloture_status_date',
        'account_name': 'awi_links__account__account_name',
        'warehouse_name': 'awi_links__warehouse__warehouse_name',

        # Filtres complémentaires (non nécessairement affichés en colonne)
        'reference': 'reference',
        'inventory_type': 'inventory_type',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
        'count_mode': 'countings__count_mode',
    }

    def get_datatable_filter(self) -> IDataTableFilter:
        """Filtre unifié qui gère automatiquement tout"""
        composite_filter = CompositeDataTableFilter()
        
        # Filtre Django Filter si configuré
        if self.filterset_class:
            composite_filter.add_filter(DjangoFilterDataTableFilter(self.filterset_class))
        
        # Filtre de mapping qui gère automatiquement tous les opérateurs
        mapping_filter = FilterMappingFilter(self.filter_aliases)
        composite_filter.add_filter(mapping_filter)
        
        return composite_filter



# Exemples d'utilisation de ServerSideDataTableView pour différents cas d'usage

class SimpleInventoryListView(ServerSideDataTableView):
    """
    Exemple simple - configuration minimale
    Supporte automatiquement : tri, recherche, pagination
    """
    model = Inventory
    serializer_class = InventoryDetailSerializer
    search_fields = ['label', 'reference']
    order_fields = ['id', 'label', 'created_at']

class AdvancedInventoryListView(ServerSideDataTableView):
    """
    Exemple avancé - avec tous les types de filtres
    Supporte : tri, recherche, filtres django-filter, filtres de date, filtres de statut
    """
    model = Inventory
    serializer_class = InventoryDetailSerializer
    filterset_class = InventoryFilter
    search_fields = ['label', 'reference', 'status', 'inventory_type']
    order_fields = ['id', 'reference', 'label', 'date', 'status', 'inventory_type', 'created_at']
    default_order = '-created_at'
    page_size = 50
    filter_fields = ['status', 'inventory_type']
    date_fields = ['date', 'created_at']
    status_fields = ['status']

class CustomInventoryListView(ServerSideDataTableView):
    """
    Exemple avec personnalisation avancée
    Surcharge des méthodes pour comportement personnalisé
    """
    model = Inventory
    serializer_class = InventoryDetailSerializer
    search_fields = ['label', 'reference', 'status']
    order_fields = ['id', 'label', 'created_at']
    
    def get_datatable_queryset(self):
        """Queryset personnalisé - seulement les inventaires non supprimés"""
        return Inventory.objects.filter(is_deleted=False)
    
    def get_datatable_config(self):
        """Configuration personnalisée"""
        config = super().get_datatable_config()
        # Personnaliser la configuration si nécessaire
        return config

class InventoryOrderingTestView(APIView):
    """Vue de test pour vérifier le tri"""
    
    def get(self, request):
        """Teste différents paramètres de tri"""
        from apps.core.datatables.base import DataTableProcessor
        
        # Créer une instance de InventoryListView pour récupérer la configuration
        inventory_view = InventoryListView()
        queryset = inventory_view.get_datatable_queryset()
        config = inventory_view.get_datatable_config()
        
        # Test avec différents paramètres de tri
        test_params = [
            ('ordering=label', 'Tri par label'),
            ('ordering=-label', 'Tri par label décroissant'),
            ('order[0][column]=2&order[0][dir]=asc', 'Tri DataTable colonne 2'),
            ('order[0][column]=2&order[0][dir]=desc', 'Tri DataTable colonne 2 décroissant'),
        ]
        
        results = []
        for param, description in test_params:
            # Créer une requête de test
            from django.test import RequestFactory
            factory = RequestFactory()
            test_request = factory.get(f'/test/?{param}')
            
            # Appliquer le tri
            processor = DataTableProcessor(
                config=config,
                filter_handler=inventory_view.get_datatable_filter(),
                serializer_handler=inventory_view.get_datatable_serializer()
            )
            
            # Tester le tri
            try:
                response = processor.process(test_request, queryset)
                results.append({
                    'param': param,
                    'description': description,
                    'success': True,
                    'response': response.content.decode()[:200] + '...'
                })
            except Exception as e:
                results.append({
                    'param': param,
                    'description': description,
                    'success': False,
                    'error': str(e)
                })
        
        return Response({
            'test_results': results,
            'order_fields': config.get_order_fields(),
            'default_order': config.get_default_order()
        })

class InventoryCreateView(APIView):
    """
    Vue pour créer un inventaire en utilisant la structure Interface, Service, Serializer, Repository, Use Cases.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ..services.inventory_management_service import InventoryManagementService
        from ..serializers.inventory_serializer import InventoryCreateSerializer
        self.service = InventoryManagementService()
        self.serializer_class = InventoryCreateSerializer

    def post(self, request, *args, **kwargs):
        """
        Crée un inventaire en utilisant la structure complète.
        """
        try:
            print(request.data)
            # ÉTAPE 1: Validation des données avec le serializer
            serializer = self.serializer_class(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Données invalides lors de la création d'un inventaire: {serializer.errors}")
                return validation_error_response(
                    serializer.errors,
                    message="Erreur de validation lors de la création de l'inventaire"
                )
            
            # ÉTAPE 2: Validation métier avec le service
            try:
                self.service.validate_create_data(serializer.validated_data)
            except InventoryValidationError as e:
                logger.warning(f"Erreur de validation métier lors de la création: {str(e)}")
                return error_response(
                    message=str(e),
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # ÉTAPE 3: Création avec le service (qui utilise le use case)
            result = self.service.create_inventory(serializer.validated_data)
            
            # ÉTAPE 4: Retour de la réponse standardisée
            return success_response(
                data=result,
                message="Inventaire créé avec succès",
                status_code=status.HTTP_201_CREATED
            )
            
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de la création: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de la création d'un inventaire: {str(e)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue s'est produite lors de la création de l'inventaire",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InventoryDuplicateView(APIView):
    """
    Vue pour dupliquer un inventaire existant en utilisant la configuration de comptages source.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ..services.inventory_duplication_service import InventoryDuplicationService
        self.service = InventoryDuplicationService()
        self.serializer_class = InventoryDuplicateSerializer

    def post(self, request, pk, *args, **kwargs):
        """
        Duplique un inventaire en conservant la configuration des comptages.
        """
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            logger.warning(
                "Données invalides lors de la duplication d'un inventaire: %s",
                serializer.errors
            )
            return validation_error_response(
                serializer.errors,
                message="Erreur de validation lors de la duplication de l'inventaire"
            )

        try:
            result = self.service.duplicate_inventory(pk, serializer.validated_data)
            return success_response(
                data=result,
                message="Inventaire dupliqué avec succès",
                status_code=status.HTTP_201_CREATED
            )
        except InventoryNotFoundError as e:
            logger.warning(
                "Inventaire source introuvable pour la duplication (id=%s): %s",
                pk,
                str(e)
            )
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except InventoryValidationError as e:
            logger.warning(
                "Erreur métier lors de la duplication d'inventaire (id=%s): %s",
                pk,
                str(e)
            )
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                "Erreur inattendue lors de la duplication d'inventaire (id=%s): %s",
                pk,
                str(e),
                exc_info=True
            )
            return error_response(
                message="Une erreur inattendue s'est produite lors de la duplication de l'inventaire",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InventoryDetailView(APIView):
    """
    Vue pour récupérer les détails d'un inventaire avec informations complètes des warehouses.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository = InventoryRepository()

    def get(self, request, pk, *args, **kwargs):
        """
        Récupère les détails d'un inventaire avec informations complètes des warehouses.
        """
        try:
            inventory = self.repository.get_with_related_data(pk)
            serializer = InventoryDetailWithWarehouseSerializer(inventory)
            return success_response(
                data=serializer.data,
                message="Détails de l'inventaire récupérés avec succès"
            )
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails d'un inventaire: {str(e)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue s'est produite lors de la récupération des détails de l'inventaire",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class InventoryDetailByReferenceView(APIView):
    """
    Vue pour récupérer les détails d'un inventaire par sa référence avec informations complètes des warehouses.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def get(self, request, reference, *args, **kwargs):
        """
        Récupère les détails d'un inventaire par sa référence avec informations complètes des warehouses.
        """
        try:
            inventory = self.service.get_inventory_with_related_data_by_reference(reference)
            serializer = InventoryDetailWithWarehouseSerializer(inventory)
            return success_response(
                data=serializer.data,
                message="Détails de l'inventaire récupérés avec succès"
            )
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails d'un inventaire: {str(e)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue s'est produite lors de la récupération des détails de l'inventaire",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class InventoryUpdateView(APIView):
    """
    Vue pour mettre à jour un inventaire en utilisant la structure Interface, Service, Serializer, Repository, Use Cases.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ..services.inventory_management_service import InventoryManagementService
        self.service = InventoryManagementService()
        self.serializer_class = InventoryUpdateSerializer

    def put(self, request, pk, *args, **kwargs):
        """
        Met à jour un inventaire en utilisant la structure complète.
        """
        try:
            # ÉTAPE 1: Validation des données avec le serializer
            serializer = self.serializer_class(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Données invalides lors de la mise à jour d'un inventaire: {serializer.errors}")
                return validation_error_response(
                    serializer.errors,
                    message="Erreur de validation lors de la mise à jour de l'inventaire"
                )
            
            # ÉTAPE 2: Validation métier avec le service
            try:
                self.service.validate_update_data(serializer.validated_data)
            except InventoryValidationError as e:
                logger.warning(f"Erreur de validation métier lors de la mise à jour: {str(e)}")
                return error_response(
                    message=str(e),
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # ÉTAPE 3: Mise à jour avec le service (qui utilise le use case)
            result = self.service.update_inventory(pk, serializer.validated_data)
            
            # ÉTAPE 4: Retour de la réponse standardisée
            return success_response(
                data=result,
                message="Inventaire mis à jour avec succès"
            )
            
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de la mise à jour: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de la mise à jour: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour d'un inventaire: {str(e)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue s'est produite lors de la mise à jour de l'inventaire",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
            return success_response(
                message="L'inventaire a été supprimé avec succès"
            )
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de la suppression: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de la suppression: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de la suppression d'un inventaire: {str(e)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue s'est produite lors de la suppression de l'inventaire",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
            # Validation métier avant lancement via le service
            validation_result = self.service.validate_launch_inventory(pk)
            self.service.launch_inventory(pk)
            
            # Préparer la réponse avec les informations de validation
            extra_data = {}
            if validation_result and 'infos' in validation_result:
                extra_data['infos'] = validation_result['infos']
            
            return success_response(
                message="L'inventaire a été lancé avec succès",
                **extra_data
            )
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors du lancement: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors du lancement: {str(e)}")
            # Séparer les erreurs multiples si elles sont séparées par " | "
            error_message = str(e)
            if " | " in error_message:
                errors = error_message.split(" | ")
                return error_response(
                    message="Plusieurs erreurs de validation ont été détectées",
                    errors=errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            else:
                return error_response(
                    message=error_message,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Erreur lors du lancement de l'inventaire: {str(e)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue s'est produite lors du lancement de l'inventaire",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
            return success_response(
                message="L'inventaire a été annulé avec succès"
            )
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de l'annulation: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de l'annulation: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de l'inventaire: {str(e)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue s'est produite lors de l'annulation de l'inventaire",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
            inventory = self.repository.get_with_related_data(pk)
            serializer = InventoryDetailModeFieldsSerializer(inventory)
            return success_response(
                data=serializer.data,
                message="Détails de l'inventaire récupérés avec succès"
            )
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails de l'inventaire: {str(e)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue s'est produite lors de la récupération des détails de l'inventaire",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
            
            return success_response(
                data=serializer.data,
                message='Statistiques des warehouses récupérées avec succès',
                warehouses_count=len(stats_data)
            )
            
        except InventoryNotFoundError as e:
            return error_response(
                message='Inventaire non trouvé',
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        except InventoryValidationError as e:
            return error_response(
                message='Erreur de validation',
                errors=[str(e)],
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques des warehouses: {str(e)}")
            return error_response(
                message='Erreur lors de la récupération des statistiques des warehouses',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InventoryResultByWarehouseView(ServerSideDataTableView):
    """
    Vue permettant de récupérer les résultats d'un inventaire agrégés par entrepôt.
    Supporte à la fois l'API REST normale et DataTable ServerSide.
    
    FONCTIONNALITÉS AUTOMATIQUES:
    - Tri sur tous les champs configurés (ordering=field ou -field)
    - Tri DataTable (order[0][column]=index&order[0][dir]=asc/desc)
    - Recherche sur champs multiples
    - Pagination optimisée
    - Sérialisation flexible
    
    PARAMÈTRES DE REQUÊTE SUPPORTÉS:
    - Tri: ordering=location, ordering=-location_id, ordering=product
    - Tri DataTable: order[0][column]=0&order[0][dir]=asc
    - Recherche: search=terme
    - Pagination: page=1&page_size=25
    """
    
    # Configuration de base
    serializer_class = InventoryWarehouseResultSerializer
    
    # Champs de recherche et tri
    search_fields = [
        'location', 'product', 'product_description', 'product_internal_code',
        'job_reference', 'final_result'
    ]
    order_fields = [
        'location', 'location_id', 'product', 'product_description',
        'job_id', 'job_reference', 'final_result', 'resolved'
    ]
    default_order = 'location'
    
    # Mapping des colonnes DataTable vers les champs réels
    # Les clés correspondent aux valeurs de columns[X][data] dans la requête DataTable
    column_field_mapping = {
        'id': 'location_id',
        'article': 'product',
        'emplacement': 'location',
        'contage_1': '1er comptage',
        'contage_2': '2er comptage',
        'contage_3': '3er comptage',
        'ecart_1_2': 'ecart_1_2',
        'ecart_2_3': 'ecart_2_3',
        'resultats': 'final_result',
    }
    
    # Configuration de pagination
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryResultService()
    
    def _get_results_data(self, inventory_id: int, warehouse_id: int) -> list:
        """
        Récupère les données brutes depuis le service.
        
        Returns:
            Liste de dictionnaires contenant les résultats
        """
        return self.service.get_inventory_results_for_warehouse(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id,
        )
    
    def _apply_search_on_list(self, data_list: list, search_term: str) -> list:
        """
        Applique la recherche sur une liste de dictionnaires.
        
        Args:
            data_list: Liste de dictionnaires à filtrer
            search_term: Terme de recherche
            
        Returns:
            Liste filtrée
        """
        if not search_term:
            return data_list
        
        search_clean = search_term.lower().strip()
        if not search_clean:
            return data_list
        
        filtered = []
        for item in data_list:
            # Rechercher dans tous les champs de recherche
            for field in self.search_fields:
                value = item.get(field)
                if value is not None and search_clean in str(value).lower():
                    filtered.append(item)
                    break
        
        return filtered
    
    def _get_field_name_from_column(self, column_index: int, request) -> str:
        """
        Obtient le nom du champ réel à partir de l'index de colonne DataTable.
        
        Args:
            column_index: Index de la colonne DataTable
            request: Requête HTTP
            
        Returns:
            Nom du champ réel
        """
        # Essayer de récupérer le nom de la colonne depuis columns[X][data]
        column_data = request.GET.get(f'columns[{column_index}][data]', '')
        if column_data and column_data in self.column_field_mapping:
            return self.column_field_mapping[column_data]
        
        # Fallback: utiliser l'index directement si dans order_fields
        if 0 <= column_index < len(self.order_fields):
            return self.order_fields[column_index]
        
        # Par défaut
        return self.default_order.lstrip('-')
    
    def _apply_ordering_on_list(self, data_list: list, ordering: str) -> list:
        """
        Applique le tri sur une liste de dictionnaires.
        
        Args:
            data_list: Liste de dictionnaires à trier
            ordering: Champ de tri (ex: 'location', '-location_id', '1er comptage')
            
        Returns:
            Liste triée
        """
        if not ordering:
            ordering = self.default_order
        
        reverse = ordering.startswith('-')
        field = ordering.lstrip('-')
        
        def sort_key(item):
            value = item.get(field)
            # Gérer les valeurs None
            if value is None:
                # Pour les champs numériques, utiliser 0 ou une grande valeur
                # Pour les champs texte, utiliser chaîne vide ou 'zzz'
                if field.endswith(' comptage') or field.startswith('ecart_') or field in ['final_result', 'location_id', 'job_id']:
                    return float('-inf') if not reverse else float('inf')
                return '' if not reverse else 'zzz'
            
            # Pour les champs numériques, convertir en nombre
            if field.endswith(' comptage') or field.startswith('ecart_') or field in ['final_result', 'location_id', 'job_id']:
                try:
                    return float(value) if value is not None else (float('-inf') if not reverse else float('inf'))
                except (ValueError, TypeError):
                    return float('-inf') if not reverse else float('inf')
            
            # Pour les champs texte, convertir en string
            return str(value).lower()
        
        return sorted(data_list, key=sort_key, reverse=reverse)
    
    def handle_datatable_request(self, request, inventory_id: int, warehouse_id: int, *args, **kwargs):
        """
        Gère les requêtes DataTable avec traitement sur liste de dictionnaires.
        """
        try:
            # Récupérer les données depuis le service
            results = self._get_results_data(inventory_id, warehouse_id)
            logger.debug(f"Données récupérées: {len(results)} résultats")
            
            # Appliquer la recherche
            search_term = request.GET.get('search', {}).get('value', '') if isinstance(request.GET.get('search'), dict) else request.GET.get('search', '')
            if not search_term:
                # Essayer aussi le format simple
                search_term = request.GET.get('search', '')
            
            if search_term:
                logger.debug(f"Recherche appliquée: '{search_term}'")
                results = self._apply_search_on_list(results, search_term)
                logger.debug(f"Après recherche: {len(results)} résultats")
            
            # Appliquer le tri DataTable
            # DataTable peut envoyer plusieurs ordres (order[0], order[1], etc.)
            ordering_applied = False
            order_index = 0
            
            # Log tous les paramètres order pour débogage
            order_params = {k: v for k, v in request.GET.items() if k.startswith('order')}
            logger.debug(f"Paramètres de tri DataTable: {order_params}")
            
            while f'order[{order_index}][column]' in request.GET:
                try:
                    column_index = int(request.GET.get(f'order[{order_index}][column]', 0))
                    direction = request.GET.get(f'order[{order_index}][dir]', 'asc')
                    
                    # Obtenir le nom du champ réel depuis le mapping
                    field = self._get_field_name_from_column(column_index, request)
                    ordering = f"-{field}" if direction == 'desc' else field
                    
                    logger.info(f"Tri DataTable appliqué: colonne {column_index} -> champ '{field}' direction '{direction}'")
                    results = self._apply_ordering_on_list(results, ordering)
                    ordering_applied = True
                    order_index += 1
                except (ValueError, IndexError) as e:
                    logger.warning(f"Erreur lors du tri DataTable: {e}", exc_info=True)
                    break
            
            # Si aucun tri DataTable n'a été appliqué, utiliser le tri par défaut
            if not ordering_applied:
                logger.debug(f"Aucun tri DataTable détecté, utilisation du tri par défaut: '{self.default_order}'")
                results = self._apply_ordering_on_list(results, self.default_order)
            
            # Pagination DataTable
            try:
                start = int(request.GET.get('start', 0))
                length = int(request.GET.get('length', self.page_size))
                length = min(max(self.min_page_size, length), self.max_page_size)
            except (ValueError, TypeError):
                start = 0
                length = self.page_size
            
            total_count = len(results)
            paginated_results = results[start:start + length]
            
            # Sérialisation
            serializer = self.serializer_class({"success": True, "data": paginated_results})
            serialized_data = serializer.data.get('data', [])
            
            # Réponse DataTable
            draw = int(request.GET.get('draw', 1))
            return Response({
                'draw': draw,
                'recordsTotal': total_count,
                'recordsFiltered': total_count,
                'data': serialized_data
            })
            
        except InventoryNotFoundError as error:
            logger.warning(
                "Inventaire introuvable lors de la récupération des résultats "
                "(inventory_id=%s, warehouse_id=%s).",
                inventory_id,
                warehouse_id,
            )
            return error_response(
                message=str(error),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except InventoryValidationError as error:
            logger.warning(
                "Erreur de validation lors de l'agrégation des résultats "
                "(inventory_id=%s, warehouse_id=%s): %s",
                inventory_id,
                warehouse_id,
                error,
            )
            return error_response(
                message=str(error),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as error:
            logger.error(
                "Erreur inattendue lors de la récupération des résultats de l'inventaire "
                "(inventory_id=%s, warehouse_id=%s): %s",
                inventory_id,
                warehouse_id,
                error,
                exc_info=True,
            )
            return error_response(
                message="Une erreur inattendue est survenue lors de la récupération des résultats",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def handle_rest_request(self, request, inventory_id: int, warehouse_id: int, *args, **kwargs):
        """
        Gère les requêtes REST API normales avec pagination simple.
        """
        try:
            # Récupérer les données depuis le service
            results = self._get_results_data(inventory_id, warehouse_id)
            
            # Appliquer la recherche
            search_term = request.GET.get('search', '')
            if search_term:
                results = self._apply_search_on_list(results, search_term)
            
            # Appliquer le tri REST API
            ordering = request.GET.get('ordering', self.default_order)
            results = self._apply_ordering_on_list(results, ordering)
            
            # Pagination REST API
            try:
                page = max(1, int(request.GET.get('page', 1)))
                page_size = min(max(self.min_page_size, int(request.GET.get('page_size', self.page_size))), self.max_page_size)
            except (ValueError, TypeError):
                page = 1
                page_size = self.page_size
            
            start = (page - 1) * page_size
            end = start + page_size
            paginated_results = results[start:end]
            
            # Sérialisation
            serializer = self.serializer_class({"success": True, "data": paginated_results})
            
            total_count = len(results)
            return Response({
                'count': total_count,
                'results': serializer.data.get('data', []),
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            })
            
        except InventoryNotFoundError as error:
            logger.warning(
                "Inventaire introuvable lors de la récupération des résultats "
                "(inventory_id=%s, warehouse_id=%s).",
                inventory_id,
                warehouse_id,
            )
            return error_response(
                message=str(error),
                status_code=status.HTTP_404_NOT_FOUND
            )
        except InventoryValidationError as error:
            logger.warning(
                "Erreur de validation lors de l'agrégation des résultats "
                "(inventory_id=%s, warehouse_id=%s): %s",
                inventory_id,
                warehouse_id,
                error,
            )
            return error_response(
                message=str(error),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as error:
            logger.error(
                "Erreur inattendue lors de la récupération des résultats de l'inventaire "
                "(inventory_id=%s, warehouse_id=%s): %s",
                inventory_id,
                warehouse_id,
                error,
                exc_info=True,
            )
            return error_response(
                message="Une erreur inattendue est survenue lors de la récupération des résultats",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class InventoryImportView(APIView):
    """
    Vue pour importer des inventaires via API.
    Permet l'importation en lot d'inventaires avec validation et création.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def post(self, request, *args, **kwargs):
        """
        Importe des inventaires en lot.
        
        Format JSON attendu:
        {
            "inventories": [
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
            ],
            "options": {
                "validate_only": false,
                "stop_on_error": true,
                "return_details": true
            }
        }
        """
        try:
            # Validation du format de la requête
            if 'inventories' not in request.data:
                return error_response(
                    message='Le champ "inventories" est requis',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            inventories_data = request.data['inventories']
            options = request.data.get('options', {})
            
            if not isinstance(inventories_data, list):
                return error_response(
                    message='Le champ "inventories" doit être une liste',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Options d'importation
            validate_only = options.get('validate_only', False)
            stop_on_error = options.get('stop_on_error', True)
            return_details = options.get('return_details', True)
            
            results = []
            errors = []
            success_count = 0
            error_count = 0
            
            for index, inventory_data in enumerate(inventories_data):
                try:
                    # Validation du serializer pour chaque inventaire
                    serializer = InventoryCreateSerializer(data=inventory_data)
                    if not serializer.is_valid():
                        error_msg = f"Inventaire {index + 1}: Erreurs de validation - {serializer.errors}"
                        errors.append({
                            'index': index,
                            'data': inventory_data,
                            'errors': serializer.errors
                        })
                        error_count += 1
                        
                        if stop_on_error:
                            break
                        continue
                    
                    if validate_only:
                        # Validation uniquement
                        result = {
                            'index': index,
                            'status': 'validated',
                            'message': f'Inventaire {index + 1} validé avec succès'
                        }
                        success_count += 1
                    else:
                        # Création de l'inventaire
                        result = self.service.create_inventory(serializer.validated_data)
                        result['index'] = index
                        result['status'] = 'created'
                        success_count += 1
                    
                    if return_details:
                        results.append(result)
                    
                except InventoryValidationError as e:
                    error_msg = f"Inventaire {index + 1}: Erreur de validation - {str(e)}"
                    errors.append({
                        'index': index,
                        'data': inventory_data,
                        'error': str(e)
                    })
                    error_count += 1
                    
                    if stop_on_error:
                        break
                        
                except Exception as e:
                    error_msg = f"Inventaire {index + 1}: Erreur inattendue - {str(e)}"
                    logger.error(f"Erreur lors de l'importation de l'inventaire {index + 1}: {str(e)}", exc_info=True)
                    errors.append({
                        'index': index,
                        'data': inventory_data,
                        'error': str(e)
                    })
                    error_count += 1
                    
                    if stop_on_error:
                        break
            
            # Préparation de la réponse
            summary = {
                'total': len(inventories_data),
                'success_count': success_count,
                'error_count': error_count
            }
            
            # Détermination du code de statut
            if error_count == 0:
                status_code = status.HTTP_201_CREATED
                message = 'Tous les inventaires ont été importés avec succès'
            elif success_count > 0:
                status_code = status.HTTP_207_MULTI_STATUS
                message = f'{success_count} inventaire(s) importé(s) avec succès, {error_count} erreur(s)'
            else:
                status_code = status.HTTP_400_BAD_REQUEST
                message = 'Aucun inventaire n\'a pu être importé'
            
            response_data = {
                'summary': summary
            }
            
            if return_details:
                if results:
                    response_data['results'] = results
                if errors:
                    response_data['errors'] = errors
            
            if error_count == 0:
                return success_response(
                    data=response_data,
                    message=message,
                    status_code=status_code
                )
            else:
                return error_response(
                    message=message,
                    errors=[err.get('error', 'Erreur inconnue') for err in errors] if errors else [],
                    status_code=status_code,
                    **response_data
                )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'importation des inventaires: {str(e)}", exc_info=True)
            return error_response(
                message='Une erreur inattendue s\'est produite lors de l\'importation',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class InventoryCompleteView(APIView):
    """
    Vue pour finaliser un inventaire.
    Marque un inventaire comme terminé uniquement si tous ses jobs sont terminés.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def post(self, request, pk, *args, **kwargs):
        """
        Finalise un inventaire en vérifiant que tous les jobs sont terminés.
        Retourne la liste des jobs non terminés si l'inventaire ne peut pas être finalisé.
        
        Args:
            pk: L'ID de l'inventaire à finaliser
            
        Returns:
            Response: Réponse HTTP avec le statut de l'opération et la liste des jobs non terminés
        """
        try:
            # Finaliser l'inventaire via le service
            result = self.service.complete_inventory(pk)
            
            # Si l'inventaire a été finalisé avec succès
            if result['success']:
                # Sérialiser l'inventaire mis à jour
                serializer = InventoryDetailSerializer(result['inventory'])
                
                return success_response(
                    data=serializer.data,
                    message=result['message'],
                    jobs_not_completed=[],
                    total_jobs=result['total_jobs'],
                    completed_jobs=result['completed_jobs']
                )
            
            # Si l'inventaire n'a pas pu être finalisé (jobs non terminés)
            else:
                return error_response(
                    message=result['message'],
                    errors=[f"Job {job.get('reference', job.get('id', 'inconnu'))} non terminé" for job in result.get('jobs_not_completed', [])],
                    status_code=status.HTTP_400_BAD_REQUEST,
                    jobs_not_completed=result['jobs_not_completed'],
                    total_jobs=result['total_jobs'],
                    completed_jobs=result['completed_jobs']
                )
            
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de la finalisation: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de la finalisation: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la finalisation de l'inventaire: {str(e)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue s'est produite lors de la finalisation de l'inventaire",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class InventoryCloseView(APIView):
    """
    Vue pour clôturer un inventaire.
    Marque un inventaire comme clôturé uniquement s'il est déjà terminé.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = InventoryService()

    def post(self, request, pk, *args, **kwargs):
        """
        Clôture un inventaire en vérifiant qu'il est déjà terminé.
        
        Args:
            pk: L'ID de l'inventaire à clôturer
            
        Returns:
            Response: Réponse HTTP avec le statut de l'opération
        """
        try:
            # Clôturer l'inventaire via le service
            inventory = self.service.close_inventory(pk)
            
            # Sérialiser l'inventaire mis à jour
            serializer = InventoryDetailSerializer(inventory)
            
            return success_response(
                data=serializer.data,
                message="L'inventaire a été marqué comme clôturé avec succès"
            )
            
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de la clôture: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de la clôture: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la clôture de l'inventaire: {str(e)}", exc_info=True)
            return error_response(
                message="Une erreur inattendue s'est produite lors de la clôture de l'inventaire",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StockImportView(APIView):
    """
    Vue pour importer des stocks via API.
    Permet l'importation de stocks depuis un fichier Excel pour un inventaire spécifique.
    Vérifie le type d'inventaire et applique les règles métier appropriées.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ..services.stock_service import StockService
        from ..usecases.stock_import_validation import StockImportValidationUseCase
        self.stock_service = StockService()
        self.validation_use_case = StockImportValidationUseCase()

    def post(self, request, inventory_id, *args, **kwargs):
        """
        Importe des stocks depuis un fichier Excel pour un inventaire spécifique.
        
        Règles métier:
        - Inventaire TOURNANT: Un seul import autorisé (refusé si stocks existants)
        - Inventaire GENERAL: Import autorisé (remplace les stocks existants)
        
        Args:
            inventory_id: L'ID de l'inventaire
            request.FILES['file']: Le fichier Excel à importer
            
        Format attendu du fichier Excel:
        - Colonnes requises: 'article', 'emplacement', 'quantite'
        - 'article': Référence du produit
        - 'emplacement': Référence de l'emplacement
        - 'quantite': Quantité disponible
        """
        try:
            # Vérifier qu'un fichier a été fourni
            if 'file' not in request.FILES:
                return error_response(
                    message='Aucun fichier fourni. Utilisez le champ "file" pour uploader le fichier Excel.',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            excel_file = request.FILES['file']
            
            # Vérifier l'extension du fichier
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                return error_response(
                    message='Le fichier doit être au format Excel (.xlsx ou .xls)',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # ÉTAPE 1: Validation selon le type d'inventaire via le use case
            validation_result = self.validation_use_case.validate_stock_import(inventory_id)
            
            # Si l'import n'est pas autorisé, retourner l'erreur
            if not validation_result['can_import']:
                return error_response(
                    message=validation_result['message'],
                    status_code=status.HTTP_400_BAD_REQUEST,
                    inventory_type=validation_result['inventory_type'],
                    existing_stocks_count=validation_result['existing_stocks_count'],
                    action_required=validation_result['action_required']
                )
            
            # ÉTAPE 2: Si l'import est autorisé, procéder à l'import
            result = self.stock_service.import_stocks_from_excel(inventory_id, excel_file)
            
            # Préparer la réponse
            summary = {
                'total_rows': result['total_rows'],
                'valid_rows': result['valid_rows'],
                'invalid_rows': result['invalid_rows']
            }
            
            extra_data = {
                'inventory_type': validation_result['inventory_type'],
                'summary': summary
            }
            
            if result.get('imported_stocks'):
                extra_data['imported_stocks'] = result['imported_stocks']
            
            if result['success']:
                return success_response(
                    data=extra_data,
                    message=result['message'],
                    status_code=status.HTTP_201_CREATED
                )
            else:
                return error_response(
                    message=result['message'],
                    errors=result.get('errors', []),
                    status_code=status.HTTP_400_BAD_REQUEST,
                    **extra_data
                )
            
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de l'import de stocks: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        except StockValidationError as e:
            logger.warning(f"Erreur de validation lors de l'import de stocks: {str(e)}")
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import de stocks: {str(e)}", exc_info=True)
            return error_response(
                message='Une erreur inattendue s\'est produite lors de l\'import',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 

 