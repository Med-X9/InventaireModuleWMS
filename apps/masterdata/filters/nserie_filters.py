import django_filters
from django_filters import rest_framework as filters
from ..models import NSerie
from django.utils import timezone
from datetime import timedelta

class NSerieFilter(filters.FilterSet):
    """
    Filtres pour les numéros de série
    """
    
    # Filtres de base
    n_serie = filters.CharFilter(lookup_expr='icontains', help_text='Recherche par numéro de série')
    description = filters.CharFilter(lookup_expr='icontains', help_text='Recherche par description')
    
    # Filtres par produit
    product_id = filters.NumberFilter(field_name='product__id', help_text='Filtrer par ID du produit')
    product_reference = filters.CharFilter(field_name='product__reference', lookup_expr='icontains', help_text='Filtrer par référence du produit')
    product_name = filters.CharFilter(field_name='product__Short_Description', lookup_expr='icontains', help_text='Filtrer par nom du produit')
    
    # Filtres par emplacement (non disponible - pas de champ location dans NSerie)
    # location_id = filters.NumberFilter(field_name='location__id', help_text='Filtrer par ID de l\'emplacement')
    # location_reference = filters.CharFilter(field_name='location__location_reference', lookup_expr='icontains', help_text='Filtrer par référence de l\'emplacement')
    
    # Filtres par statut
    status = filters.ChoiceFilter(choices=NSerie.STATUS_CHOICES, help_text='Filtrer par statut')
    
    # Filtres par dates
    date_fabrication_from = filters.DateFilter(field_name='date_fabrication', lookup_expr='gte', help_text='Date de fabrication à partir de')
    date_fabrication_to = filters.DateFilter(field_name='date_fabrication', lookup_expr='lte', help_text='Date de fabrication jusqu\'à')
    
    date_expiration_from = filters.DateFilter(field_name='date_expiration', lookup_expr='gte', help_text='Date d\'expiration à partir de')
    date_expiration_to = filters.DateFilter(field_name='date_expiration', lookup_expr='lte', help_text='Date d\'expiration jusqu\'à')
    
    warranty_end_date_from = filters.DateFilter(field_name='warranty_end_date', lookup_expr='gte', help_text='Date de fin de garantie à partir de')
    warranty_end_date_to = filters.DateFilter(field_name='warranty_end_date', lookup_expr='lte', help_text='Date de fin de garantie jusqu\'à')
    
    # Filtres par quantité (à implémenter si nécessaire)
    # stock_quantity_min = filters.NumberFilter(field_name='stock_quantity', lookup_expr='gte', help_text='Quantité en stock minimum')
    # stock_quantity_max = filters.NumberFilter(field_name='stock_quantity', lookup_expr='lte', help_text='Quantité en stock maximum')
    
    # Filtres par suivi (à implémenter si nécessaire)
    # is_tracked = filters.BooleanFilter(help_text='Filtrer par suivi activé/désactivé')
    
    # Filtres spéciaux
    expired = filters.BooleanFilter(method='filter_expired', help_text='Filtrer les numéros de série expirés')
    expiring_soon = filters.BooleanFilter(method='filter_expiring_soon', help_text='Filtrer les numéros de série qui expirent bientôt')
    warranty_expired = filters.BooleanFilter(method='filter_warranty_expired', help_text='Filtrer les numéros de série dont la garantie est expirée')
    
    # Filtres par date de création
    created_at_from = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', help_text='Date de création à partir de')
    created_at_to = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', help_text='Date de création jusqu\'à')
    
    # Filtres par date de mise à jour
    updated_at_from = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte', help_text='Date de mise à jour à partir de')
    updated_at_to = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte', help_text='Date de mise à jour jusqu\'à')
    
    class Meta:
        model = NSerie
        fields = {
            'reference': ['exact', 'icontains'],
            'n_serie': ['exact', 'icontains', 'startswith', 'endswith'],
            'status': ['exact'],
        }
    
    def filter_expired(self, queryset, name, value):
        """
        Filtre les numéros de série expirés
        """
        today = timezone.now().date()
        if value:
            return queryset.filter(date_expiration__lt=today)
        else:
            return queryset.filter(
                django_filters.Q(date_expiration__gte=today) | 
                django_filters.Q(date_expiration__isnull=True)
            )
    
    def filter_expiring_soon(self, queryset, name, value):
        """
        Filtre les numéros de série qui expirent bientôt (dans les 30 jours)
        """
        today = timezone.now().date()
        future_date = today + timedelta(days=30)
        
        if value:
            return queryset.filter(
                date_expiration__gte=today,
                date_expiration__lte=future_date
            )
        else:
            return queryset.filter(
                django_filters.Q(date_expiration__lt=today) | 
                django_filters.Q(date_expiration__gt=future_date) |
                django_filters.Q(date_expiration__isnull=True)
            )
    
    def filter_warranty_expired(self, queryset, name, value):
        """
        Filtre les numéros de série dont la garantie est expirée
        """
        today = timezone.now().date()
        if value:
            return queryset.filter(warranty_end_date__lt=today)
        else:
            return queryset.filter(
                django_filters.Q(warranty_end_date__gte=today) | 
                django_filters.Q(warranty_end_date__isnull=True)
            ) 