from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ..models import NSerie, Product
from ..serializers.product_serializer import (
    NSerieSerializer, NSerieCreateSerializer, NSerieUpdateSerializer,
    NSerieListSerializer, NSerieDetailSerializer, ProductNSerieSerializer
)
from ..services.nserie_service import NSerieService
from ..filters.nserie_filters import NSerieFilter
from apps.core.datatables.mixins import ServerSideDataTableView

class NSeriePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000

class NSerieListView(ServerSideDataTableView):
    """
    Vue pour lister tous les numéros de série avec pagination et filtres DataTable.
    """
    model = NSerie
    serializer_class = NSerieListSerializer
    filterset_class = NSerieFilter
    search_fields = ['n_serie', 'description', 'product__Short_Description', 'product__Internal_Product_Code']
    order_fields = ['created_at', 'n_serie', 'status', 'date_expiration', 'warranty_end_date']
    default_order = '-created_at'
    page_size = 20
    min_page_size = 1
    max_page_size = 1000

class NSerieDetailView(RetrieveAPIView):
    """
    Vue pour récupérer les détails d'un numéro de série
    """
    queryset = NSerie.objects.all()
    serializer_class = NSerieDetailSerializer
    lookup_field = 'id'

class NSerieCreateView(CreateAPIView):
    """
    Vue pour créer un nouveau numéro de série
    """
    serializer_class = NSerieCreateSerializer
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                nserie_service = NSerieService()
                nserie = nserie_service.create_nserie(serializer.validated_data)
                
                return Response({
                    'success': True,
                    'message': 'Numéro de série créé avec succès',
                    'data': NSerieDetailSerializer(nserie).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Erreur de validation',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NSerieUpdateView(UpdateAPIView):
    """
    Vue pour mettre à jour un numéro de série
    """
    queryset = NSerie.objects.all()
    serializer_class = NSerieUpdateSerializer
    lookup_field = 'id'
    
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            
            if serializer.is_valid():
                nserie_service = NSerieService()
                updated_nserie = nserie_service.update_nserie(instance.id, serializer.validated_data)
                
                return Response({
                    'success': True,
                    'message': 'Numéro de série mis à jour avec succès',
                    'data': NSerieDetailSerializer(updated_nserie).data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Erreur de validation',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NSerieDeleteView(DestroyAPIView):
    """
    Vue pour supprimer un numéro de série (soft delete)
    """
    queryset = NSerie.objects.all()
    lookup_field = 'id'
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            nserie_service = NSerieService()
            success = nserie_service.delete_nserie(instance.id)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Numéro de série supprimé avec succès'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Erreur lors de la suppression'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NSerieByProductView(ServerSideDataTableView):
    """
    Vue pour lister les numéros de série d'un produit spécifique - Support DataTable.
    """
    model = NSerie
    serializer_class = NSerieListSerializer
    search_fields = ['n_serie', 'description']
    order_fields = ['created_at', 'n_serie', 'status', 'date_expiration']
    default_order = '-created_at'
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    
    def get_datatable_queryset(self):
        product_id = self.kwargs.get('product_id')
        nserie_service = NSerieService()
        return nserie_service.get_nseries_by_product(product_id)

class NSerieByLocationView(ServerSideDataTableView):
    """
    Vue pour lister les numéros de série d'un emplacement spécifique - Support DataTable.
    Note: Cette vue n'est pas disponible car NSerie n'a pas de champ location
    """
    model = NSerie
    serializer_class = NSerieListSerializer
    search_fields = ['n_serie', 'description', 'product__Short_Description']
    order_fields = ['created_at', 'n_serie', 'status', 'date_expiration']
    default_order = '-created_at'
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    
    def get_datatable_queryset(self):
        # Cette vue n'est pas disponible car NSerie n'a pas de champ location
        return NSerie.objects.none()

class NSerieByStatusView(ServerSideDataTableView):
    """
    Vue pour lister les numéros de série par statut - Support DataTable.
    """
    model = NSerie
    serializer_class = NSerieListSerializer
    search_fields = ['n_serie', 'description', 'product__Short_Description']
    order_fields = ['created_at', 'n_serie', 'date_expiration']
    default_order = '-created_at'
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    
    def get_datatable_queryset(self):
        status = self.kwargs.get('status')
        nserie_service = NSerieService()
        return nserie_service.get_nseries_by_status(status)

class NSerieExpiredView(ServerSideDataTableView):
    """
    Vue pour lister les numéros de série expirés - Support DataTable.
    """
    model = NSerie
    serializer_class = NSerieListSerializer
    search_fields = ['n_serie', 'description', 'product__Short_Description']
    order_fields = ['date_expiration', 'created_at', 'n_serie']
    default_order = 'date_expiration'
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    
    def get_datatable_queryset(self):
        nserie_service = NSerieService()
        return nserie_service.get_expired_nseries()

class NSerieExpiringView(ServerSideDataTableView):
    """
    Vue pour lister les numéros de série qui expirent bientôt - Support DataTable.
    """
    model = NSerie
    serializer_class = NSerieListSerializer
    search_fields = ['n_serie', 'description', 'product__Short_Description']
    order_fields = ['date_expiration', 'created_at', 'n_serie']
    default_order = 'date_expiration'
    page_size = 20
    min_page_size = 1
    max_page_size = 1000
    
    def get_datatable_queryset(self):
        days = self.request.query_params.get('days', 30)
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        nserie_service = NSerieService()
        return nserie_service.get_expiring_nseries(days)

class NSerieStatisticsView(APIView):
    """
    Vue pour récupérer les statistiques des numéros de série
    """
    def get(self, request):
        try:
            nserie_service = NSerieService()
            statistics = nserie_service.get_nserie_statistics()
            
            return Response({
                'success': True,
                'data': statistics
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NSerieMoveToLocationView(APIView):
    """
    Vue pour déplacer un numéro de série vers un nouvel emplacement
    Note: Cette vue n'est pas disponible car NSerie n'a pas de champ location
    """
    def post(self, request, nserie_id):
        return Response({
            'success': False,
            'message': 'Cette fonctionnalité n\'est pas disponible car NSerie n\'a pas de champ location'
        }, status=status.HTTP_400_BAD_REQUEST)

class NSerieUpdateStatusView(APIView):
    """
    Vue pour mettre à jour le statut d'un numéro de série
    """
    def post(self, request, nserie_id):
        try:
            status = request.data.get('status')
            if not status:
                return Response({
                    'success': False,
                    'message': 'status est requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            nserie_service = NSerieService()
            updated_nserie = nserie_service.update_nserie_status(nserie_id, status)
            
            return Response({
                'success': True,
                'message': 'Statut mis à jour avec succès',
                'data': NSerieDetailSerializer(updated_nserie).data
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Erreur interne : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductWithNSerieView(RetrieveAPIView):
    """
    Vue pour récupérer un produit avec ses numéros de série
    """
    queryset = Product.objects.filter(n_serie=True)
    serializer_class = ProductNSerieSerializer
    lookup_field = 'id' 