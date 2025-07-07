from django_filters import rest_framework as filters
from ..models import Job, JobDetail, Assigment, JobDetailRessource
from django.db.models import Count

class JobFilter(filters.FilterSet):
    created_at_gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_lte = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    status = filters.CharFilter(field_name='status', lookup_expr='exact')
    warehouse = filters.NumberFilter(field_name='warehouse', lookup_expr='exact')
    inventory = filters.NumberFilter(field_name='inventory', lookup_expr='exact')
    reference = filters.CharFilter(field_name='reference', lookup_expr='icontains')
    en_attente_date_gte = filters.DateTimeFilter(field_name='en_attente_date', lookup_expr='gte')
    en_attente_date_lte = filters.DateTimeFilter(field_name='en_attente_date', lookup_expr='lte')
    valide_date_gte = filters.DateTimeFilter(field_name='valide_date', lookup_expr='gte')
    valide_date_lte = filters.DateTimeFilter(field_name='valide_date', lookup_expr='lte')
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
            'en_attente_date', 'valide_date', 'termine_date',
            'location_reference', 'sous_zone', 'zone'
        ]

class JobFullDetailFilter(filters.FilterSet):
    reference = filters.CharFilter(field_name='reference', lookup_expr='icontains')
    status = filters.CharFilter(field_name='status', lookup_expr='icontains')
    emplacement_reference = filters.CharFilter(method='filter_emplacement_reference')
    sous_zone = filters.CharFilter(method='filter_sous_zone')
    zone = filters.CharFilter(method='filter_zone')
    session_username = filters.CharFilter(method='filter_session_username')
    ressource_reference = filters.CharFilter(method='filter_ressource_reference')
    assignment_status = filters.CharFilter(method='filter_assignment_status')
    counting_order = filters.NumberFilter(method='filter_counting_order')

    class Meta:
        model = Job
        fields = []

    def filter_emplacement_reference(self, queryset, name, value):
        return queryset.filter(jobdetail__location__location_reference__icontains=value)
    def filter_sous_zone(self, queryset, name, value):
        return queryset.filter(jobdetail__location__sous_zone__sous_zone_name__icontains=value)
    def filter_zone(self, queryset, name, value):
        return queryset.filter(jobdetail__location__sous_zone__zone__zone_name__icontains=value)
    def filter_session_username(self, queryset, name, value):
        return queryset.filter(assigment__session__username__icontains=value)
    def filter_ressource_reference(self, queryset, name, value):
        return queryset.filter(jobdetailressource__ressource__reference__icontains=value)
    def filter_assignment_status(self, queryset, name, value):
        return queryset.filter(assigment__status__icontains=value)
    def filter_counting_order(self, queryset, name, value):
        return queryset.filter(assigment__counting__order=value)

class PendingJobFilter(filters.FilterSet):
    """
    Filtre pour les jobs en attente
    """
    reference = filters.CharFilter(lookup_expr='icontains', help_text="Recherche par référence de job")
    inventory_id = filters.NumberFilter(field_name='inventory__id', help_text="Filtrer par ID d'inventaire")
    inventory_reference = filters.CharFilter(field_name='inventory__reference', lookup_expr='icontains', help_text="Recherche par référence d'inventaire")
    inventory_label = filters.CharFilter(field_name='inventory__label', lookup_expr='icontains', help_text="Recherche par label d'inventaire")
    warehouse_id = filters.NumberFilter(field_name='warehouse__id', help_text="Filtrer par ID d'entrepôt")
    warehouse_reference = filters.CharFilter(field_name='warehouse__reference', lookup_expr='icontains', help_text="Recherche par référence d'entrepôt")
    warehouse_name = filters.CharFilter(field_name='warehouse__warehouse_name', lookup_expr='icontains', help_text="Recherche par nom d'entrepôt")
    created_at_gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', help_text="Date de création >= (format: YYYY-MM-DD HH:MM:SS)")
    created_at_lte = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', help_text="Date de création <= (format: YYYY-MM-DD HH:MM:SS)")
    created_at_date = filters.DateFilter(field_name='created_at', lookup_expr='date', help_text="Date de création exacte (format: YYYY-MM-DD)")
    emplacements_count_min = filters.NumberFilter(method='filter_emplacements_count_min', help_text="Nombre minimum d'emplacements")
    emplacements_count_max = filters.NumberFilter(method='filter_emplacements_count_max', help_text="Nombre maximum d'emplacements")
    assignments_count_min = filters.NumberFilter(method='filter_assignments_count_min', help_text="Nombre minimum d'assignations")
    assignments_count_max = filters.NumberFilter(method='filter_assignments_count_max', help_text="Nombre maximum d'assignations")

    class Meta:
        model = Job
        fields = {
            'reference': ['exact', 'icontains'],
            'inventory__id': ['exact'],
            'inventory__reference': ['exact', 'icontains'],
            'inventory__label': ['exact', 'icontains'],
            'warehouse__id': ['exact'],
            'warehouse__reference': ['exact', 'icontains'],
            'warehouse__warehouse_name': ['exact', 'icontains'],
            'created_at': ['exact', 'gte', 'lte', 'date'],
        }

    def filter_emplacements_count_min(self, queryset, name, value):
        """Filtre par nombre minimum d'emplacements"""
        return queryset.annotate(
            emplacements_count=Count('jobdetail')
        ).filter(emplacements_count__gte=value)

    def filter_emplacements_count_max(self, queryset, name, value):
        """Filtre par nombre maximum d'emplacements"""
        return queryset.annotate(
            emplacements_count=Count('jobdetail')
        ).filter(emplacements_count__lte=value)

    def filter_assignments_count_min(self, queryset, name, value):
        """Filtre par nombre minimum d'assignations"""
        return queryset.annotate(
            assignments_count=Count('assigment')
        ).filter(assignments_count__gte=value)

    def filter_assignments_count_max(self, queryset, name, value):
        """Filtre par nombre maximum d'assignations"""
        return queryset.annotate(
            assignments_count=Count('assigment')
        ).filter(assignments_count__lte=value) 