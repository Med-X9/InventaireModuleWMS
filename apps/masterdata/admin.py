from django.contrib import admin

# Register your models here.
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import (
    Account, Family, Warehouse, ZoneType, Zone,
    LocationType, Location, Product, UnitOfMeasure
)
from django.contrib.auth.admin import UserAdmin
from apps.users.models import UserWeb
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



@admin.register(UserWeb)
class UserWebAdmin(UserAdmin):
    list_display = ('nom', 'prenom', 'username', 'email', 'role', 'type', 'is_staff', 'is_active')
    list_filter = ('role', 'type', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'nom', 'prenom')
    ordering = ('username',)

    

    filter_horizontal = ('groups', 'user_permissions')

    # Champs à afficher dans le formulaire d’édition
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'prenom', 'role', 'type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login',)}),
    )

    # Champs à afficher dans le formulaire de création
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'nom', 'prenom', 'role', 'type', 'password1', 'password2', 'is_staff', 'is_superuser', 'groups')}
        ),
    )

    








@admin.register(Account)
class AccountAdmin(ImportExportModelAdmin):
    resource_class = AccountResource
    list_display = ('account_code', 'account_name', 'account_statuts')
    search_fields = ('account_code', 'account_name', 'account_statuts')
    list_filter = ('account_statuts',)
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted')


@admin.register(Family)
class FamilyAdmin(ImportExportModelAdmin):
    resource_class = FamilyResource
    list_display = ('family_code', 'family_name', 'family_status')
    search_fields = ('family_code', 'family_name', 'family_status')
    list_filter = ('family_status',)
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted')


@admin.register(Warehouse)
class WarehouseAdmin(ImportExportModelAdmin):
    resource_class = WarehouseResource
    list_display = ('warehouse_code', 'warehouse_name', 'warehouse_type', 'status')
    search_fields = ('warehouse_code', 'warehouse_name', 'warehouse_type', 'status')
    list_filter = ('warehouse_type', 'status')
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted')


@admin.register(ZoneType)
class ZoneTypeAdmin(ImportExportModelAdmin):
    resource_class = ZoneTypeResource
    list_display = ('type_code', 'type_name', 'status')
    search_fields = ('type_code', 'type_name', 'status')
    list_filter = ('status',)
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted')


@admin.register(Zone)
class ZoneAdmin(ImportExportModelAdmin):
    resource_class = ZoneResource
    list_display = ('zone_code', 'zone_name', 'warehouse_id', 'zone_type_id', 'zone_status')
    search_fields = ('zone_code', 'zone_name', 'zone_status')
    list_filter = ('zone_status', 'warehouse_id', 'zone_type_id')
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted')


@admin.register(LocationType)
class LocationTypeAdmin(ImportExportModelAdmin):
    resource_class = LocationTypeResource
    list_display = ('code', 'name', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('is_active',)
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted')


@admin.register(Location)
class LocationAdmin(ImportExportModelAdmin):
    resource_class = LocationResource
    list_display = ('location_code', 'zone_id', 'location_type_id', 'capacity', 'is_active')
    search_fields = ('location_code',)
    list_filter = ('zone_id', 'location_type_id', 'is_active')
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted')


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = ('reference', 'Short_Description', 'Barcode', 'Product_Group', 'Stock_Unit', 'Product_Status', 'Is_Variant')
    search_fields = ('reference', 'Short_Description', 'Barcode', 'Product_Group', 'Stock_Unit')
    list_filter = ('Product_Status', 'Is_Variant')
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted')


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(ImportExportModelAdmin):
    resource_class = UnitOfMeasureResource
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted')
