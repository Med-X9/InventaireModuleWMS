from django.urls import path
from .views.location_views import AllWarehouseLocationListView, WarehouseJobLocationsView, SousZoneLocationsView
from .views.warehouse_views import WarehouseListView
from .views.account_views import AccountListView
from django.conf.urls.i18n import set_language
from .views.zone_view import ZoneListView, ZoneDetailView
from .views.sous_zone_view import SousZoneListView, SousZoneDetailView, ZoneSousZonesView

app_name = 'masterdata'

urlpatterns = [
    # Exemple de route
    path('set_language/', set_language, name='set_language'),
    path('accounts/', AccountListView.as_view(), name='account-list'),
    path('warehouses/', WarehouseListView.as_view(), name='warehouse-list'),
    path('warehouse/<int:warehouse_id>/locations/', AllWarehouseLocationListView.as_view(), name='warehouse-locations'),
    path('warehouse/<int:warehouse_id>/job-locations/', WarehouseJobLocationsView.as_view(), name='warehouse-job-locations'),
    
    # Routes pour les zones
    path('zones/', ZoneListView.as_view(), name='zone-list'),
    path('zones/<int:pk>/', ZoneDetailView.as_view(), name='zone-detail'),
    path('zones/<int:zone_id>/sous-zones/', ZoneSousZonesView.as_view(), name='zone-sous-zones'),
    
    # Routes pour les sous-zones
    path('sous-zones/', SousZoneListView.as_view(), name='sous-zone-list'),
    path('sous-zones/<int:pk>/', SousZoneDetailView.as_view(), name='sous-zone-detail'),
    path('sous-zones/<int:sous_zone_id>/locations/', SousZoneLocationsView.as_view(), name='sous-zone-locations'),
]
