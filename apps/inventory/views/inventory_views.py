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
    InventoryWarehouseStatsSerializer,
    InventoryUpdateSerializer,
    InventoryDetailModeFieldsSerializer,
    InventoryDetailWithWarehouseSerializer
)
from ..exceptions import InventoryValidationError, InventoryNotFoundError, StockValidationError
from ..filters import InventoryFilter
from ..repositories import InventoryRepository
from ..interfaces import IInventoryRepository
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
    max_page_size = 100
    
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
    
    # Mapping ultra-simple : 1 champ frontend = 1 champ Django
    filter_aliases = {
        'label': 'label',
        'reference': 'reference',
        'status': 'status',
        'inventory_type': 'inventory_type',
        'date': 'date',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
        'account': 'awi_links__account__account_name',
        'warehouse': 'awi_links__warehouse__warehouse_name',
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
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ÉTAPE 2: Validation métier avec le service
            try:
                self.service.validate_create_data(serializer.validated_data)
            except InventoryValidationError as e:
                logger.warning(f"Erreur de validation métier lors de la création: {str(e)}")
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ÉTAPE 3: Création avec le service (qui utilise le use case)
            result = self.service.create_inventory(serializer.validated_data)
            
            # ÉTAPE 4: Retour de la réponse
            return Response(result, status=status.HTTP_201_CREATED)
            
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de la création: {str(e)}")
            return Response(
                {"error": str(e)},
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
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ÉTAPE 2: Validation métier avec le service
            try:
                self.service.validate_update_data(serializer.validated_data)
            except InventoryValidationError as e:
                logger.warning(f"Erreur de validation métier lors de la mise à jour: {str(e)}")
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ÉTAPE 3: Mise à jour avec le service (qui utilise le use case)
            result = self.service.update_inventory(pk, serializer.validated_data)
            
            # ÉTAPE 4: Retour de la réponse
            return Response(result, status=status.HTTP_200_OK)
            
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de la mise à jour: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de la mise à jour: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
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
            # Validation métier avant lancement via le service
            validation_result = self.service.validate_launch_inventory(pk)
            self.service.launch_inventory(pk)
            
            # Préparer la réponse avec les informations de validation
            response_data = {
                "message": "L'inventaire a été lancé avec succès"
            }
            
            # Ajouter les messages d'information s'ils existent
            if validation_result and 'infos' in validation_result:
                response_data['infos'] = validation_result['infos']
            
            return Response(response_data, status=status.HTTP_200_OK)
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors du lancement: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors du lancement: {str(e)}")
            # Séparer les erreurs multiples si elles sont séparées par " | "
            error_message = str(e)
            if " | " in error_message:
                errors = error_message.split(" | ")
                return Response({
                    "errors": errors,
                    "message": "Plusieurs erreurs de validation ont été détectées"
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
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
            inventory = self.repository.get_with_related_data(pk)
            serializer = InventoryDetailModeFieldsSerializer(inventory)
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
                return Response({
                    'success': False,
                    'message': 'Le champ "inventories" est requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            inventories_data = request.data['inventories']
            options = request.data.get('options', {})
            
            if not isinstance(inventories_data, list):
                return Response({
                    'success': False,
                    'message': 'Le champ "inventories" doit être une liste'
                }, status=status.HTTP_400_BAD_REQUEST)
            
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
            response_data = {
                'success': error_count == 0 or not stop_on_error,
                'summary': {
                    'total': len(inventories_data),
                    'success_count': success_count,
                    'error_count': error_count
                }
            }
            
            if return_details:
                if results:
                    response_data['results'] = results
                if errors:
                    response_data['errors'] = errors
            
            # Détermination du code de statut
            if error_count == 0:
                status_code = status.HTTP_201_CREATED
            elif success_count > 0:
                status_code = status.HTTP_207_MULTI_STATUS
            else:
                status_code = status.HTTP_400_BAD_REQUEST
            
            return Response(response_data, status=status_code)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'importation des inventaires: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Une erreur inattendue s\'est produite lors de l\'importation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                
                return Response({
                    "success": True,
                    "message": result['message'],
                    "data": serializer.data,
                    "jobs_not_completed": [],
                    "total_jobs": result['total_jobs'],
                    "completed_jobs": result['completed_jobs']
                }, status=status.HTTP_200_OK)
            
            # Si l'inventaire n'a pas pu être finalisé (jobs non terminés)
            else:
                return Response({
                    "success": False,
                    "message": result['message'],
                    "jobs_not_completed": result['jobs_not_completed'],
                    "total_jobs": result['total_jobs'],
                    "completed_jobs": result['completed_jobs'],
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de la finalisation: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
            
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de la finalisation: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur lors de la finalisation de l'inventaire: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            
            return Response({
                "message": "L'inventaire a été marqué comme clôturé avec succès",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de la clôture: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
            
        except InventoryValidationError as e:
            logger.warning(f"Erreur de validation lors de la clôture: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur lors de la clôture de l'inventaire: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                return Response({
                    'success': False,
                    'message': 'Aucun fichier fourni. Utilisez le champ "file" pour uploader le fichier Excel.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            excel_file = request.FILES['file']
            
            # Vérifier l'extension du fichier
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                return Response({
                    'success': False,
                    'message': 'Le fichier doit être au format Excel (.xlsx ou .xls)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ÉTAPE 1: Validation selon le type d'inventaire via le use case
            validation_result = self.validation_use_case.validate_stock_import(inventory_id)
            
            # Si l'import n'est pas autorisé, retourner l'erreur
            if not validation_result['can_import']:
                return Response({
                    'success': False,
                    'message': validation_result['message'],
                    'inventory_type': validation_result['inventory_type'],
                    'existing_stocks_count': validation_result['existing_stocks_count'],
                    'action_required': validation_result['action_required']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ÉTAPE 2: Si l'import est autorisé, procéder à l'import
            result = self.stock_service.import_stocks_from_excel(inventory_id, excel_file)
            
            # Préparer la réponse
            if result['success']:
                response_data = {
                    'success': True,
                    'message': result['message'],
                    'inventory_type': validation_result['inventory_type'],
                    'summary': {
                        'total_rows': result['total_rows'],
                        'valid_rows': result['valid_rows'],
                        'invalid_rows': result['invalid_rows']
                    }
                }
                
                # Ajouter les détails des stocks importés si disponibles
                if result.get('imported_stocks'):
                    response_data['imported_stocks'] = result['imported_stocks']
                
                status_code = status.HTTP_201_CREATED
            else:
                response_data = {
                    'success': False,
                    'message': result['message'],
                    'inventory_type': validation_result['inventory_type'],
                    'summary': {
                        'total_rows': result['total_rows'],
                        'valid_rows': result['valid_rows'],
                        'invalid_rows': result['invalid_rows']
                    },
                    'errors': result.get('errors', [])
                }
                status_code = status.HTTP_400_BAD_REQUEST
            
            return Response(response_data, status=status_code)
            
        except InventoryNotFoundError as e:
            logger.warning(f"Inventaire non trouvé lors de l'import de stocks: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
            
        except StockValidationError as e:
            logger.warning(f"Erreur de validation lors de l'import de stocks: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import de stocks: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Une erreur inattendue s\'est produite lors de l\'import'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

 