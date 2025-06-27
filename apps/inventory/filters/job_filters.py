from django_filters import rest_framework as filters
from ..models import Job, JobDetail

class JobFilter(filters.FilterSet):
    created_at_gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_lte = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    status = filters.CharFilter(field_name='status', lookup_expr='exact')
    warehouse = filters.NumberFilter(field_name='warehouse', lookup_expr='exact')
    inventory = filters.NumberFilter(field_name='inventory', lookup_expr='exact')
    reference = filters.CharFilter(field_name='reference', lookup_expr='icontains')
    date_estime_gte = filters.DateTimeFilter(field_name='date_estime', lookup_expr='gte')
    date_estime_lte = filters.DateTimeFilter(field_name='date_estime', lookup_expr='lte')
    transfert_date_gte = filters.DateTimeFilter(field_name='transfert_date', lookup_expr='gte')
    transfert_date_lte = filters.DateTimeFilter(field_name='transfert_date', lookup_expr='lte')
    en_attente_date_gte = filters.DateTimeFilter(field_name='en_attente_date', lookup_expr='gte')
    en_attente_date_lte = filters.DateTimeFilter(field_name='en_attente_date', lookup_expr='lte')
    entame_date_gte = filters.DateTimeFilter(field_name='entame_date', lookup_expr='gte')
    entame_date_lte = filters.DateTimeFilter(field_name='entame_date', lookup_expr='lte')
    valide_date_gte = filters.DateTimeFilter(field_name='valide_date', lookup_expr='gte')
    valide_date_lte = filters.DateTimeFilter(field_name='valide_date', lookup_expr='lte')
    affecte_date_gte = filters.DateTimeFilter(field_name='affecte_date', lookup_expr='gte')
    affecte_date_lte = filters.DateTimeFilter(field_name='affecte_date', lookup_expr='lte')
    pret_date_gte = filters.DateTimeFilter(field_name='pret_date', lookup_expr='gte')
    pret_date_lte = filters.DateTimeFilter(field_name='pret_date', lookup_expr='lte')
    termine_date_gte = filters.DateTimeFilter(field_name='termine_date', lookup_expr='gte')
    termine_date_lte = filters.DateTimeFilter(field_name='termine_date', lookup_expr='lte')

    # Filtres imbriqués sur les emplacements (JobDetail -> Location)
    location_reference = filters.CharFilter(field_name='jobdetail__location__location_reference', lookup_expr='icontains')
    sous_zone = filters.NumberFilter(field_name='jobdetail__location__sous_zone', lookup_expr='exact')
    zone = filters.NumberFilter(field_name='jobdetail__location__sous_zone__zone', lookup_expr='exact')

    class Meta:
        model = Job
        fields = [
            'status', 'warehouse', 'inventory', 'reference', 'created_at',
            'date_estime', 'transfert_date', 'en_attente_date', 'entame_date',
            'valide_date', 'affecte_date', 'pret_date', 'termine_date',
            'location_reference', 'sous_zone', 'zone'
        ] 