from django_filters import rest_framework as filters
from ..models import Inventory, Setting, Counting

class InventoryFilter(filters.FilterSet):
    """
    Filtres pour l'inventaire - Tous les champs disponibles
    """
    # Filtres de base
    reference = filters.CharFilter(field_name='reference', lookup_expr='icontains')
    label = filters.CharFilter(field_name='label', lookup_expr='icontains')
    status = filters.ChoiceFilter(choices=Inventory.STATUS_CHOICES)
    
    # Filtres de date
    date_gte = filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    date_lte = filters.DateTimeFilter(field_name='date', lookup_expr='lte')
    date_exact = filters.DateTimeFilter(field_name='date', lookup_expr='exact')
    
    # Filtres de dates de statut
    en_preparation_status_date_gte = filters.DateTimeFilter(field_name='en_preparation_status_date', lookup_expr='gte')
    en_preparation_status_date_lte = filters.DateTimeFilter(field_name='en_preparation_status_date', lookup_expr='lte')
    en_preparation_status_date_exact = filters.DateTimeFilter(field_name='en_preparation_status_date', lookup_expr='exact')
    
    en_realisation_status_date_gte = filters.DateTimeFilter(field_name='en_realisation_status_date', lookup_expr='gte')
    en_realisation_status_date_lte = filters.DateTimeFilter(field_name='en_realisation_status_date', lookup_expr='lte')
    en_realisation_status_date_exact = filters.DateTimeFilter(field_name='en_realisation_status_date', lookup_expr='exact')
    
    ternime_status_date_gte = filters.DateTimeFilter(field_name='ternime_status_date', lookup_expr='gte')
    ternime_status_date_lte = filters.DateTimeFilter(field_name='ternime_status_date', lookup_expr='lte')
    ternime_status_date_exact = filters.DateTimeFilter(field_name='ternime_status_date', lookup_expr='exact')
    
    cloture_status_date_gte = filters.DateTimeFilter(field_name='cloture_status_date', lookup_expr='gte')
    cloture_status_date_lte = filters.DateTimeFilter(field_name='cloture_status_date', lookup_expr='lte')
    cloture_status_date_exact = filters.DateTimeFilter(field_name='cloture_status_date', lookup_expr='exact')
    
    # Filtres pour les relations (account et warehouse)
    account_name = filters.CharFilter(field_name='awi_links__account__account_name', lookup_expr='icontains')
    account_id = filters.NumberFilter(field_name='awi_links__account__id', lookup_expr='exact')
    warehouse_name = filters.CharFilter(field_name='awi_links__warehouse__warehouse_name', lookup_expr='icontains')
    warehouse_id = filters.NumberFilter(field_name='awi_links__warehouse__id', lookup_expr='exact')
    
    # Filtres pour les comptages
    count_mode = filters.CharFilter(field_name='countings__count_mode', lookup_expr='icontains')
    count_mode_exact = filters.CharFilter(field_name='countings__count_mode', lookup_expr='exact')
    counting_order = filters.NumberFilter(field_name='countings__order', lookup_expr='exact')
    
    # Filtres pour les champs de création/modification
    created_at_gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_lte = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    created_at_exact = filters.DateTimeFilter(field_name='created_at', lookup_expr='exact')
    
    updated_at_gte = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_at_lte = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    updated_at_exact = filters.DateTimeFilter(field_name='updated_at', lookup_expr='exact')
    
    # Filtres pour les champs booléens des comptages
    unit_scanned = filters.BooleanFilter(field_name='countings__unit_scanned', lookup_expr='exact')
    entry_quantity = filters.BooleanFilter(field_name='countings__entry_quantity', lookup_expr='exact')
    is_variant = filters.BooleanFilter(field_name='countings__is_variant', lookup_expr='exact')
    n_lot = filters.BooleanFilter(field_name='countings__n_lot', lookup_expr='exact')
    n_serie = filters.BooleanFilter(field_name='countings__n_serie', lookup_expr='exact')
    dlc = filters.BooleanFilter(field_name='countings__dlc', lookup_expr='exact')
    show_product = filters.BooleanFilter(field_name='countings__show_product', lookup_expr='exact')
    stock_situation = filters.BooleanFilter(field_name='countings__stock_situation', lookup_expr='exact')
    quantity_show = filters.BooleanFilter(field_name='countings__quantity_show', lookup_expr='exact')

    class Meta:
        model = Inventory
        fields = {
            'reference': ['exact', 'icontains'],
            'label': ['exact', 'icontains'],
            'status': ['exact'],
            'date': ['exact', 'gte', 'lte'],
            'en_preparation_status_date': ['exact', 'gte', 'lte'],
            'en_realisation_status_date': ['exact', 'gte', 'lte'],
            'ternime_status_date': ['exact', 'gte', 'lte'],
            'cloture_status_date': ['exact', 'gte', 'lte'],
            'created_at': ['exact', 'gte', 'lte'],
            'updated_at': ['exact', 'gte', 'lte'],
        } 