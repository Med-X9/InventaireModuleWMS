from django.urls import path
from .views.location_views import AllWarehouseLocationListView, WarehouseJobLocationsView
from .views.warehouse_views import WarehouseListView
from .views.account_views import AccountListView
from django.conf.urls.i18n import set_language

app_name = 'masterdata'

urlpatterns = [
    # Exemple de route
    path('set_language/', set_language, name='set_language'),
    path('accounts/', AccountListView.as_view(), name='account-list'),
    path('warehouses/', WarehouseListView.as_view(), name='warehouse-list'),
    path('warehouse/<int:warehouse_id>/locations/', AllWarehouseLocationListView.as_view(), name='warehouse-locations'),
    path('warehouse/<int:warehouse_id>/job-locations/', WarehouseJobLocationsView.as_view(), name='warehouse-job-locations'),
]
