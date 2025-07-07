from django_filters import rest_framework as filters
from ..models import Location, SousZone, Zone, Warehouse
from django.db.models import Count

class UnassignedLocationFilter(filters.FilterSet):
    """
    Filtre pour les emplacements non affectés
    """
    # Filtres de base
    reference = filters.CharFilter(lookup_expr='icontains', help_text="Recherche par référence d'emplacement")
    location_reference = filters.CharFilter(lookup_expr='icontains', help_text="Recherche par référence d'emplacement")
    description = filters.CharFilter(lookup_expr='icontains', help_text="Recherche par description")
    
    # Filtres de sous-zone
    sous_zone_id = filters.NumberFilter(field_name='sous_zone__id', help_text="Filtrer par ID de sous-zone")
    sous_zone_reference = filters.CharFilter(field_name='sous_zone__reference', lookup_expr='icontains', help_text="Recherche par référence de sous-zone")
    sous_zone_name = filters.CharFilter(field_name='sous_zone__sous_zone_name', lookup_expr='icontains', help_text="Recherche par nom de sous-zone")
    sous_zone_status = filters.CharFilter(field_name='sous_zone__sous_zone_status', lookup_expr='exact', help_text="Filtrer par statut de sous-zone")
    
    # Filtres de zone
    zone_id = filters.NumberFilter(field_name='sous_zone__zone__id', help_text="Filtrer par ID de zone")
    zone_reference = filters.CharFilter(field_name='sous_zone__zone__reference', lookup_expr='icontains', help_text="Recherche par référence de zone")
    zone_name = filters.CharFilter(field_name='sous_zone__zone__zone_name', lookup_expr='icontains', help_text="Recherche par nom de zone")
    zone_status = filters.CharFilter(field_name='sous_zone__zone__zone_status', lookup_expr='exact', help_text="Filtrer par statut de zone")
    
    # Filtres d'entrepôt
    warehouse_id = filters.NumberFilter(field_name='sous_zone__zone__warehouse__id', help_text="Filtrer par ID d'entrepôt")
    warehouse_reference = filters.CharFilter(field_name='sous_zone__zone__warehouse__reference', lookup_expr='icontains', help_text="Recherche par référence d'entrepôt")
    warehouse_name = filters.CharFilter(field_name='sous_zone__zone__warehouse__warehouse_name', lookup_expr='icontains', help_text="Recherche par nom d'entrepôt")
    warehouse_type = filters.CharFilter(field_name='sous_zone__zone__warehouse__warehouse_type', lookup_expr='exact', help_text="Filtrer par type d'entrepôt")
    warehouse_status = filters.CharFilter(field_name='sous_zone__zone__warehouse__status', lookup_expr='exact', help_text="Filtrer par statut d'entrepôt")
    
    # Filtres de date
    created_at_gte = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', help_text="Date de création >= (format: YYYY-MM-DD HH:MM:SS)")
    created_at_lte = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', help_text="Date de création <= (format: YYYY-MM-DD HH:MM:SS)")
    created_at_date = filters.DateFilter(field_name='created_at', lookup_expr='date', help_text="Date de création exacte (format: YYYY-MM-DD)")
    updated_at_gte = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte', help_text="Date de modification >= (format: YYYY-MM-DD HH:MM:SS)")
    updated_at_lte = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte', help_text="Date de modification <= (format: YYYY-MM-DD HH:MM:SS)")
    
    # Filtres de type d'emplacement
    location_type_id = filters.NumberFilter(field_name='location_type__id', help_text="Filtrer par ID de type d'emplacement")
    location_type_reference = filters.CharFilter(field_name='location_type__reference', lookup_expr='icontains', help_text="Recherche par référence de type d'emplacement")
    location_type_name = filters.CharFilter(field_name='location_type__name', lookup_expr='icontains', help_text="Recherche par nom de type d'emplacement")

    class Meta:
        model = Location
        fields = {
            'reference': ['exact', 'icontains'],
            'location_reference': ['exact', 'icontains'],
            'description': ['exact', 'icontains'],
            'is_active': ['exact'],
            'created_at': ['exact', 'gte', 'lte', 'date'],
            'updated_at': ['exact', 'gte', 'lte'],
            'sous_zone__id': ['exact'],
            'sous_zone__reference': ['exact', 'icontains'],
            'sous_zone__sous_zone_name': ['exact', 'icontains'],
            'sous_zone__sous_zone_status': ['exact'],
            'sous_zone__zone__id': ['exact'],
            'sous_zone__zone__reference': ['exact', 'icontains'],
            'sous_zone__zone__zone_name': ['exact', 'icontains'],
            'sous_zone__zone__zone_status': ['exact'],
            'sous_zone__zone__warehouse__id': ['exact'],
            'sous_zone__zone__warehouse__reference': ['exact', 'icontains'],
            'sous_zone__zone__warehouse__warehouse_name': ['exact', 'icontains'],
            'sous_zone__zone__warehouse__warehouse_type': ['exact'],
            'sous_zone__zone__warehouse__status': ['exact'],
            'location_type__id': ['exact'],
            'location_type__reference': ['exact', 'icontains'],
            'location_type__name': ['exact', 'icontains'],
        } 