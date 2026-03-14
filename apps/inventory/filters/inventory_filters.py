from django_filters import rest_framework as filters
from ..models import Inventory, Setting, Counting
from django.utils.dateparse import parse_datetime, parse_date

class InventoryFilter(filters.FilterSet):
    """
    Filtres pour l'inventaire
    """
    date_gte = filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    date_lte = filters.DateTimeFilter(field_name='date', lookup_expr='lte')
    date_exact = filters.DateTimeFilter(field_name='date', lookup_expr='exact')
    # Filtre personnalisé pour l'intervalle date/datetime
    date_interval = filters.CharFilter(method='filter_date_interval')
    label = filters.CharFilter(field_name='label', lookup_expr='icontains')
    label_contains = filters.CharFilter(field_name='label', lookup_expr='icontains')
    label_exact = filters.CharFilter(field_name='label', lookup_expr='exact')
    label_startswith = filters.CharFilter(field_name='label', lookup_expr='istartswith')
    label_endswith = filters.CharFilter(field_name='label', lookup_expr='iendswith')
    en_preparation_status_date_gte = filters.DateTimeFilter(field_name='en_preparation_status_date', lookup_expr='gte')
    en_preparation_status_date_lte = filters.DateTimeFilter(field_name='en_preparation_status_date', lookup_expr='lte')
    en_preparation_status_date_exact = filters.DateTimeFilter(field_name='en_preparation_status_date', lookup_expr='exact')
    en_preparation_status_date_interval = filters.CharFilter(method='filter_en_preparation_status_date_interval')
    en_realisation_status_date_gte = filters.DateTimeFilter(field_name='en_realisation_status_date', lookup_expr='gte')
    en_realisation_status_date_lte = filters.DateTimeFilter(field_name='en_realisation_status_date', lookup_expr='lte')
    en_realisation_status_date_exact = filters.DateTimeFilter(field_name='en_realisation_status_date', lookup_expr='exact')
    en_realisation_status_date_interval = filters.CharFilter(method='filter_en_realisation_status_date_interval')
    termine_status_date_gte = filters.DateTimeFilter(field_name='termine_status_date', lookup_expr='gte')
    termine_status_date_lte = filters.DateTimeFilter(field_name='termine_status_date', lookup_expr='lte')
    termine_status_date_exact = filters.DateTimeFilter(field_name='termine_status_date', lookup_expr='exact')
    termine_status_date_interval = filters.CharFilter(method='filter_termine_status_date_interval')
    cloture_status_date_gte = filters.DateTimeFilter(field_name='cloture_status_date', lookup_expr='gte')
    cloture_status_date_lte = filters.DateTimeFilter(field_name='cloture_status_date', lookup_expr='lte')
    cloture_status_date_exact = filters.DateTimeFilter(field_name='cloture_status_date', lookup_expr='exact')
    cloture_status_date_interval = filters.CharFilter(method='filter_cloture_status_date_interval')
    status = filters.ChoiceFilter(field_name='status', choices=Inventory.STATUS_CHOICES)
    status_in = filters.MultipleChoiceFilter(field_name='status', choices=Inventory.STATUS_CHOICES)
    # Filtres pour account et warehouse
    account = filters.CharFilter(field_name='awi_links__account__account_name', lookup_expr='icontains')
    account_contains = filters.CharFilter(field_name='awi_links__account__account_name', lookup_expr='icontains')
    warehouse = filters.CharFilter(field_name='awi_links__warehouse__warehouse_name', lookup_expr='icontains')
    warehouse_contains = filters.CharFilter(field_name='awi_links__warehouse__warehouse_name', lookup_expr='icontains')
    
    # Filtres pour reference
    reference = filters.CharFilter(field_name='reference', lookup_expr='icontains')
    reference_contains = filters.CharFilter(field_name='reference', lookup_expr='icontains')
    reference_exact = filters.CharFilter(field_name='reference', lookup_expr='exact')
    
    # Filtre pour le mode de comptage
    count_mode = filters.CharFilter(field_name='countings__count_mode', lookup_expr='icontains')
    count_mode_contains = filters.CharFilter(field_name='countings__count_mode', lookup_expr='icontains')

    def filter_date_interval(self, queryset, name, value):
        return self._filter_interval(queryset, 'date', value)

    def filter_en_preparation_status_date_interval(self, queryset, name, value):
        return self._filter_interval(queryset, 'en_preparation_status_date', value)

    def filter_en_realisation_status_date_interval(self, queryset, name, value):
        return self._filter_interval(queryset, 'en_realisation_status_date', value)

    def filter_termine_status_date_interval(self, queryset, name, value):
        return self._filter_interval(queryset, 'termine_status_date', value)

    def filter_cloture_status_date_interval(self, queryset, name, value):
        return self._filter_interval(queryset, 'cloture_status_date', value)

    def _filter_interval(self, queryset, field, value):
        if value:
            try:
                min_val, max_val = value.split(',')
                min_dt = parse_datetime(min_val) or parse_date(min_val)
                max_dt = parse_datetime(max_val) or parse_date(max_val)
                if min_dt and max_dt:
                    filter_kwargs = {f"{field}__gte": min_dt, f"{field}__lte": max_dt}
                    return queryset.filter(**filter_kwargs)
            except Exception:
                pass
        return queryset

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