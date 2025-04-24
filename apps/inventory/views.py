from django.shortcuts import render
from django.views.generic import ListView
from apps.masterdata.models import Account, Warehouse

# Create your views here.

class AccountListView(ListView):
    model = Account
    template_name = 'inventory/account_list.html'
    context_object_name = 'accounts'

class WarehouseListView(ListView):
    model = Warehouse
    template_name = 'inventory/warehouse_list.html'
    context_object_name = 'warehouses'
