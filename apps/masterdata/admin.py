from django.contrib import admin

# Register your models here.
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import (
    Account, Family, Warehouse, ZoneType, Zone,
    LocationType, Location, Product, UnitOfMeasure
)

# ---------------- Resources ---------------- #

class AccountResource(resources.ModelResource):
    class Meta:
        model = Account

class FamilyResource(resources.ModelResource):
    class Meta:
        model = Family

class WarehouseResource(resources.ModelResource):
    class Meta:
        model = Warehouse

class ZoneTypeResource(resources.ModelResource):
    class Meta:
        model = ZoneType

class ZoneResource(resources.ModelResource):
    class Meta:
        model = Zone

class LocationTypeResource(resources.ModelResource):
    class Meta:
        model = LocationType

class LocationResource(resources.ModelResource):
    class Meta:
        model = Location

class ProductResource(resources.ModelResource):
    class Meta:
        model = Product

class UnitOfMeasureResource(resources.ModelResource):
    class Meta:
        model = UnitOfMeasure



# ---------------- Admins ---------------- #

@admin.register(Account)
class AccountAdmin(ImportExportModelAdmin):
    resource_class = AccountResource
    list_display = ('account_code', 'account_name', 'account_statuts', 'created_at', 'updated_at')
    search_fields = ('account_code', 'account_name')

@admin.register(Family)
class FamilyAdmin(ImportExportModelAdmin):
    resource_class = FamilyResource
    list_display = ('family_code', 'family_name', 'family_status', 'created_at', 'updated_at')
    search_fields = ('family_code', 'family_name')
    list_filter = ('family_status',)

@admin.register(Warehouse)
class WarehouseAdmin(ImportExportModelAdmin):
    resource_class = WarehouseResource
    list_display = ('warehouse_code', 'warehouse_name', 'warehouse_type', 'status')
    list_filter = ('warehouse_type', 'status')

@admin.register(ZoneType)
class ZoneTypeAdmin(ImportExportModelAdmin):
    resource_class = ZoneTypeResource
    list_display = ('type_code', 'type_name', 'status')

@admin.register(Zone)
class ZoneAdmin(ImportExportModelAdmin):
    resource_class = ZoneResource
    list_display = ('zone_code', 'zone_name', 'warehouse_id', 'zone_type_id', 'zone_status')
    list_filter = ('zone_status',)

@admin.register(LocationType)
class LocationTypeAdmin(ImportExportModelAdmin):
    resource_class = LocationTypeResource
    list_display = ('code', 'name', 'is_active')

@admin.register(Location)
class LocationAdmin(ImportExportModelAdmin):
    resource_class = LocationResource
    list_display = ('location_code', 'zone_id', 'location_type_id', 'capacity', 'is_active')

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = ('reference', 'Short_Description', 'Barcode', 'Product_Group', 'Stock_Unit', 'Product_Status', 'Is_Variant')
    search_fields = ('reference', 'Short_Description', 'Barcode')
    list_filter = ('Product_Status', 'Is_Variant')

@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(ImportExportModelAdmin):
    resource_class = UnitOfMeasureResource
    list_display = ('code', 'name')

