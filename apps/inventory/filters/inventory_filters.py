from django_filters import rest_framework as filters
from ..models import Inventory, Setting, Counting

class InventoryFilter(filters.FilterSet):
    """
    Filtres pour l'inventaire
    """
    date_gte = filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    date_lte = filters.DateTimeFilter(field_name='date', lookup_expr='lte')
    label = filters.CharFilter(field_name='label', lookup_expr='icontains')
    en_preparation_status_date_gte = filters.DateTimeFilter(field_name='en_preparation_status_date', lookup_expr='gte')
    en_preparation_status_date_lte = filters.DateTimeFilter(field_name='en_preparation_status_date', lookup_expr='lte')
    en_realisation_status_date_gte = filters.DateTimeFilter(field_name='en_realisation_status_date', lookup_expr='gte')
    en_realisation_status_date_lte = filters.DateTimeFilter(field_name='en_realisation_status_date', lookup_expr='lte')
    termine_status_date_gte = filters.DateTimeFilter(field_name='termine_status_date', lookup_expr='gte')
    termine_status_date_lte = filters.DateTimeFilter(field_name='termine_status_date', lookup_expr='lte')
    cloture_status_date_gte = filters.DateTimeFilter(field_name='cloture_status_date', lookup_expr='gte')
    cloture_status_date_lte = filters.DateTimeFilter(field_name='cloture_status_date', lookup_expr='lte')
    
    # Filtres pour account et warehouse
    account = filters.CharFilter(field_name='awi_links__account__account_name', lookup_expr='icontains')
    warehouse = filters.CharFilter(field_name='awi_links__warehouse__warehouse_name', lookup_expr='icontains')
    
    # Filtre pour le mode de comptage
    count_mode = filters.CharFilter(field_name='countings__count_mode', lookup_expr='icontains')

    class Meta:
        model = Inventory
        fields = {
            'status': ['exact'],
            'date': ['exact'],
            'label': ['exact'],
            'en_preparation_status_date': ['exact'],
            'en_realisation_status_date': ['exact'],
            'termine_status_date': ['exact'],
            'cloture_status_date': ['exact'],
        } 