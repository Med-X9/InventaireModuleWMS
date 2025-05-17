from django_filters import rest_framework as filters
from .models import Inventory, Setting, Counting

class InventoryFilter(filters.FilterSet):
    """
    Filtres pour l'inventaire
    """
    date_gte = filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    date_lte = filters.DateTimeFilter(field_name='date', lookup_expr='lte')
    label = filters.CharFilter(field_name='label', lookup_expr='icontains')
    end_status_date_gte = filters.DateTimeFilter(field_name='end_status_date', lookup_expr='gte')
    end_status_date_lte = filters.DateTimeFilter(field_name='end_status_date', lookup_expr='lte')
    lunch_status_date_gte = filters.DateTimeFilter(field_name='lunch_status_date', lookup_expr='gte')
    lunch_status_date_lte = filters.DateTimeFilter(field_name='lunch_status_date', lookup_expr='lte')
    current_status_date_gte = filters.DateTimeFilter(field_name='current_status_date', lookup_expr='gte')
    current_status_date_lte = filters.DateTimeFilter(field_name='current_status_date', lookup_expr='lte')
    pending_status_date_gte = filters.DateTimeFilter(field_name='pending_status_date', lookup_expr='gte')
    pending_status_date_lte = filters.DateTimeFilter(field_name='pending_status_date', lookup_expr='lte')
    
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
            'end_status_date': ['exact'],
            'lunch_status_date': ['exact'],
            'current_status_date': ['exact'],
            'pending_status_date': ['exact'],
        } 