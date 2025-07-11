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
    ordering = '-created_at'  # Tri par défaut par date décroissante
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

class StockImportView(APIView):
    """
    Vue pour importer des stocks via API.
    Permet l'importation de stocks depuis un fichier Excel pour un inventaire spécifique.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ..services.stock_service import StockService
        self.stock_service = StockService()

    def post(self, request, inventory_id, *args, **kwargs):
        """
        Importe des stocks depuis un fichier Excel pour un inventaire spécifique.
        
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
            
            # Importer les stocks via le service
            result = self.stock_service.import_stocks_from_excel(inventory_id, excel_file)
            
            # Préparer la réponse
            if result['success']:
                response_data = {
                    'success': True,
                    'message': result['message'],
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
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import de stocks: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Une erreur inattendue s\'est produite lors de l\'import'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 