from django.urls import path

from apps.inventory.views.ressource_views import RessourceDetailView, RessourceListView, RessourceInventaireListView, RessourceJobListView
from .views.location_views import AllWarehouseLocationListView, WarehouseJobLocationsView, SousZoneLocationsView, UnassignedLocationsView, LocationDetailView
from .views.warehouse_views import WarehouseListView, WarehouseDetailByReferenceView
from .views.account_views import AccountListView
from .views.user_views import MobileUserListView, MobileUserDetailView, WarehouseMobileUsersView
from django.conf.urls.i18n import set_language
from .views.zone_view import ZoneListView, ZoneDetailView
from .views.sous_zone_view import SousZoneListView, SousZoneDetailView, ZoneSousZonesView
from .views.nserie_views import (
    NSerieListView, NSerieDetailView, NSerieCreateView, NSerieUpdateView, NSerieDeleteView,
    NSerieByProductView, NSerieByLocationView, NSerieByStatusView, NSerieExpiredView,
    NSerieExpiringView, NSerieStatisticsView, NSerieMoveToLocationView, NSerieUpdateStatusView,
    ProductWithNSerieView
)

app_name = 'masterdata'

urlpatterns = [
    # Exemple de route
    path('set_language/', set_language, name='set_language'),
    path('accounts/', AccountListView.as_view(), name='account-list'),
    path('warehouses/', WarehouseListView.as_view(), name='warehouse-list'),
    path('warehouses/<str:reference>/', WarehouseDetailByReferenceView.as_view(), name='warehouse-detail-by-reference'),
    path('warehouses/<int:warehouse_id>/locations/', AllWarehouseLocationListView.as_view(), name='warehouse-locations'),
    path('warehouses/<int:warehouse_id>/job-locations/', WarehouseJobLocationsView.as_view(), name='warehouse-job-locations'),
    
    # Routes pour les utilisateurs mobile
    path('users/mobile/', MobileUserListView.as_view(), name='mobile-users-list'),
    path('users/mobile/<int:user_id>/', MobileUserDetailView.as_view(), name='mobile-user-detail'),
    path('users/mobile/warehouses/<int:warehouse_id>/users/mobile/', WarehouseMobileUsersView.as_view(), name='warehouse-mobile-users'),
    
    # Routes pour les zones
    path('zones/', ZoneListView.as_view(), name='zone-list'),
    path('zones/<int:pk>/', ZoneDetailView.as_view(), name='zone-detail'),
    path('zones/<int:zone_id>/sous-zones/', ZoneSousZonesView.as_view(), name='zone-sous-zones'),
    
    # Routes pour les sous-zones
    path('sous-zones/', SousZoneListView.as_view(), name='sous-zone-list'),
    path('sous-zones/<int:pk>/', SousZoneDetailView.as_view(), name='sous-zone-detail'),
    path('sous-zones/<int:sous_zone_id>/locations/', SousZoneLocationsView.as_view(), name='sous-zone-locations'),
    
    # URLs pour les emplacements non affectés
    path('locations/unassigned/', UnassignedLocationsView.as_view(), name='unassigned-locations'),
    path('warehouses/<int:account_id>/warehouse/<int:warehouse_id>/locations/unassigned/', UnassignedLocationsView.as_view(), name='account-warehouse-unassigned-locations'),
    
    # URLs pour les emplacements
    path('locations/<int:pk>/', LocationDetailView.as_view(), name='location-detail'),
    
    # URLs pour les ressources
    path('ressources/', RessourceListView.as_view(), name='ressource-list'),
    path('ressources/<int:pk>/', RessourceDetailView.as_view(), name='ressource-detail'),
    path('ressources/inventaire/', RessourceInventaireListView.as_view(), name='ressource-inventaire-list'),
    path('ressources/job/', RessourceJobListView.as_view(), name='ressource-job-list'),
    
    # URLs pour les numéros de série
    path('nseries/', NSerieListView.as_view(), name='nserie-list'),
    path('nseries/<int:id>/', NSerieDetailView.as_view(), name='nserie-detail'),
    path('nseries/create/', NSerieCreateView.as_view(), name='nserie-create'),
    path('nseries/<int:id>/update/', NSerieUpdateView.as_view(), name='nserie-update'),
    path('nseries/<int:id>/delete/', NSerieDeleteView.as_view(), name='nserie-delete'),
    
    # URLs pour les numéros de série par produit
    path('products/<int:product_id>/nseries/', NSerieByProductView.as_view(), name='nserie-by-product'),
    path('products/<int:id>/with-nseries/', ProductWithNSerieView.as_view(), name='product-with-nseries'),
    
    # URLs pour les numéros de série par emplacement
    path('locations/<int:location_id>/nseries/', NSerieByLocationView.as_view(), name='nserie-by-location'),
    
    # URLs pour les numéros de série par statut
    path('nseries/status/<str:status>/', NSerieByStatusView.as_view(), name='nserie-by-status'),
    
    # URLs pour les numéros de série expirés
    path('nseries/expired/', NSerieExpiredView.as_view(), name='nserie-expired'),
    path('nseries/expiring/', NSerieExpiringView.as_view(), name='nserie-expiring'),
    
    # URLs pour les statistiques
    path('nseries/statistics/', NSerieStatisticsView.as_view(), name='nserie-statistics'),
    
    # URLs pour les actions spéciales
    path('nseries/<int:nserie_id>/move/', NSerieMoveToLocationView.as_view(), name='nserie-move'),
    path('nseries/<int:nserie_id>/status/', NSerieUpdateStatusView.as_view(), name='nserie-update-status'),
]
