from django.contrib import admin
from django import forms
from django.utils import timezone
import random
from datetime import datetime

# Register your models here.
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields, widgets
from import_export.formats.base_formats import XLSX, CSV, XLS

from .models import (
    Account, Family, Warehouse, ZoneType, Zone,
    LocationType, Location, Product, UnitOfMeasure,Stock,SousZone
)
from django.contrib.auth.admin import UserAdmin
from apps.users.models import UserApp
# ---------------- Resources ---------------- #

class AccountResource(resources.ModelResource):
    class Meta:
        model = Account






class FamilyResource(resources.ModelResource):
    family_name = fields.Field(column_name='family name', attribute='family_name', widget=widgets.CharWidget())
    family_status = fields.Field(column_name='family status', attribute='family_status', widget=widgets.CharWidget())
    family_description = fields.Field(column_name='family description', attribute='family_description', widget=widgets.CharWidget())
    compte = fields.Field(
            column_name='account',
            attribute='compte',
            widget=widgets.ForeignKeyWidget(Account, 'account_name')
        )
    class Meta:
        model = Family
        fields = ('family_name', 'family_status','family_description','compte')
        exclude = ('id',)
        import_id_fields = ()

    def before_import_row(self, row, **kwargs):
        # Chercher l'objet account à partir du nom dans la ligne d'importation
        account_name = row.get('account')
        # print(location_name)
        try:
            account_obj = Account.objects.get(account_name=account_name)
            # print(location_obj)
            row['account'] = account_obj
        except Account.DoesNotExist:
            raise ValueError(f"Le compte '{account_name}' n'existe pas dans la base de données.")











class WarehouseResource(resources.ModelResource):
    class Meta:
        model = Warehouse

class ZoneTypeResource(resources.ModelResource):
    class Meta:
        model = ZoneType

class ZoneResource(resources.ModelResource):
    zone_name = fields.Field(column_name='zone name', attribute='zone_name', widget=widgets.CharWidget())
    zone_status = fields.Field(column_name='zone status', attribute='zone_status', widget=widgets.CharWidget())
    description = fields.Field(column_name='description', attribute='description', widget=widgets.CharWidget())
    zone_type_id = fields.Field(
        column_name='zone type',
        attribute='zone_type_id',
        widget=widgets.ForeignKeyWidget(ZoneType, 'type_name')
    )
    warehouse_id = fields.Field(
        column_name='werhouse',
        attribute='warehouse_id',
        widget=widgets.ForeignKeyWidget(Warehouse, 'warehouse_name')
    )

    class Meta:
        model = Zone  # À corriger si c'est censé être Zone et non Family
        fields = ('zone_name', 'zone_status','description','zone_type_id','warehouse_id')
        exclude = ('id',)
        import_id_fields = ()

    def before_import_row(self, row, **kwargs):
        zone_type_name = row.get('zone type')
        warehouse_name = row.get('werhouse')  # attention ici

        if not ZoneType.objects.filter(type_name=zone_type_name).exists():
            raise ValueError(f"Le type de zone '{zone_type_name}' n'existe pas dans la base de données.")

        if not Warehouse.objects.filter(warehouse_name=warehouse_name).exists():
            raise ValueError(f"L'entrepôt '{warehouse_name}' n'existe pas dans la base de données.")


    



class SousZoneResource(resources.ModelResource):
    sous_zone_name = fields.Field(column_name='sous zone name', attribute='sous_zone_name', widget=widgets.CharWidget())
    sous_zone_status = fields.Field(column_name='sous zone status', attribute='sous_zone_status', widget=widgets.CharWidget())
    description = fields.Field(column_name='description', attribute='description', widget=widgets.CharWidget())
    zone_id = fields.Field(
        column_name='zone',
        attribute='zone_id',
        widget=widgets.ForeignKeyWidget(Zone, 'zone_name')
    )
    
    class Meta:
        model = SousZone  # À corriger si c'est censé être Zone et non Family
        fields = ('sous_zone_name', 'sous_zone_status','description','zone_id')
        exclude = ('id',)
        import_id_fields = ()

    def before_import_row(self, row, **kwargs):
        zone_name = row.get('zone')

        if not Zone.objects.filter(zone_name=zone_name).exists():
            raise ValueError(f"La zone '{zone_name}' n'existe pas dans la base de données.")

        



    
    
    
    

class LocationTypeResource(resources.ModelResource):
    class Meta:
        model = LocationType

class LocationResource(resources.ModelResource):
    capacity = fields.Field(column_name='capacity', attribute='capacity', widget=widgets.CharWidget())
    is_active = fields.Field(column_name='active', attribute='is_active', widget=widgets.CharWidget())
    description = fields.Field(column_name='description', attribute='description', widget=widgets.CharWidget())
    location_type_id = fields.Field(
            column_name='location type',
            attribute='location_type_id',
            widget=widgets.ForeignKeyWidget(LocationType, 'name')
        )
    sous_zone_id = fields.Field(
        column_name='sous zone',
        attribute='sous_zone_id',
        widget=widgets.ForeignKeyWidget(SousZone, 'sous_zone_name')
    )
    class Meta:
        model = Location
        fields = ('capacity', 'is_active','description','location_type_id','sous_zone_id')
        exclude = ('id',)
        import_id_fields = ()

    def before_import_row(self, row, **kwargs):
        # S'assurer que les noms des types de zone et entrepôt existent
        location_type_id = row.get('location type')
        sous_zone_id = row.get('sous zone')

        try:
            LocationType.objects.get(name=location_type_id)
        except LocationType.DoesNotExist:
            raise ValueError(f"Le type de location '{location_type_id}' n'existe pas dans la base de données.")

        try:
            SousZone.objects.get(sous_zone_name=sous_zone_id)
        except SousZone.DoesNotExist:
            raise ValueError(f"La sous zone '{sous_zone_id}' n'existe pas dans la base de données.")
        









        

class ProductResource(resources.ModelResource):
    reference = fields.Field(column_name='reference', attribute='reference', widget=widgets.CharWidget())
    Short_Description = fields.Field(column_name='short description', attribute='Short_Description', widget=widgets.CharWidget())
    Barcode = fields.Field(column_name='barcode', attribute='Barcode', widget=widgets.CharWidget())
    Product_Group = fields.Field(column_name='product group', attribute='Product_Group', widget=widgets.CharWidget())
    Stock_Unit = fields.Field(column_name='stock unit', attribute='Stock_Unit', widget=widgets.CharWidget())
    Product_Status = fields.Field(column_name='product status', attribute='Product_Status', widget=widgets.CharWidget())
    Internal_Product_Code = fields.Field(column_name='internal product code', attribute='Internal_Product_Code', widget=widgets.CharWidget())
    
    Product_Family = fields.Field(
        column_name='product family',
        attribute='Product_Family',
        widget=widgets.ForeignKeyWidget(Family, 'family_name')
    )

    parent_product = fields.Field(
        column_name='parent product',
        attribute='parent_product',
        widget=widgets.ForeignKeyWidget(Product, 'reference')
    )

    Is_Variant = fields.Field(column_name='is variant', attribute='Is_Variant', widget=widgets.BooleanWidget())

    class Meta:
        model = Product
        fields = (
            'reference',
            'Short_Description',
            'Barcode',
            'Product_Group',
            'Stock_Unit',
            'Product_Status',
            'Internal_Product_Code',
            'Product_Family',
            'parent_product',
            'Is_Variant',
        )
        exclude = ('id',)
        import_id_fields = ('reference',)

    def before_import_row(self, row, **kwargs):
        # Vérifier si la famille existe
        family_name = row.get('product family')
        if family_name:
            try:
                Family.objects.get(family_name=family_name)
            except Family.DoesNotExist:
                raise ValueError(f"La famille de produit '{family_name}' n'existe pas.")

        # Vérifier si le produit parent existe (si spécifié)
        parent_reference = row.get('parent product')
        if parent_reference:
            try:
                Product.objects.get(reference=parent_reference)
            except Product.DoesNotExist:
                raise ValueError(f"Le produit parent '{parent_reference}' n'existe pas.")

class UnitOfMeasureResource(resources.ModelResource):
    class Meta:
        model = UnitOfMeasure


class StockResource(resources.ModelResource):
    location = fields.Field(
        column_name='location',
        attribute='location',
        widget=widgets.ForeignKeyWidget(Location, 'location_code')
    )
    product = fields.Field(
        column_name='product',
        attribute='product',
        widget=widgets.ForeignKeyWidget(Product, 'reference')
    )
    quantity_available = fields.Field(
        column_name='quantity available',
        attribute='quantity_available',
        widget=widgets.DecimalWidget()
    )
    quantity_reserved = fields.Field(
        column_name='quantity reserved',
        attribute='quantity_reserved',
        widget=widgets.DecimalWidget()
    )
    quantity_in_transit = fields.Field(
        column_name='quantity in transit',
        attribute='quantity_in_transit',
        widget=widgets.DecimalWidget()
    )
    quantity_in_receiving = fields.Field(
        column_name='quantity in receiving',
        attribute='quantity_in_receiving',
        widget=widgets.DecimalWidget()
    )
    unit_of_measure = fields.Field(
        column_name='unit of measure',
        attribute='unit_of_measure',
        widget=widgets.ForeignKeyWidget(UnitOfMeasure, 'code')
    )

    class Meta:
        model = Stock
        fields = (
            'location',
            'product',
            'quantity_available',
            'quantity_reserved',
            'quantity_in_transit',
            'quantity_in_receiving',
            'unit_of_measure',
        )
        exclude = ('id',)
        import_id_fields = ('location', 'product')

    def before_import_row(self, row, **kwargs):
        # Vérifie que la location existe
        location_code = row.get('location')
        if location_code:
            if not Location.objects.filter(location_code=location_code).exists():
                raise ValueError(f"La localisation '{location_code}' n'existe pas.")

        # Vérifie que le produit existe
        product_ref = row.get('product')
        if product_ref:
            if not Product.objects.filter(reference=product_ref).exists():
                raise ValueError(f"Le produit '{product_ref}' n'existe pas.")

        # Vérifie que l'unité de mesure existe
        uom_code = row.get('unit of measure')
        if uom_code:
            if not UnitOfMeasure.objects.filter(code=uom_code).exists():
                raise ValueError(f"L'unité de mesure '{uom_code}' n'existe pas.")


# ---------------- Admins ---------------- #



@admin.register(UserApp)
class UserAppAdmin(UserAdmin):
    list_display = ('nom', 'prenom', 'username', 'email', 'role','is_staff', 'is_active')
    list_filter = ('role','is_staff', 'is_active')
    search_fields = ('username', 'email', 'nom', 'prenom')
    ordering = ('username',)

    

    filter_horizontal = ('groups', 'user_permissions')

    # Champs à afficher dans le formulaire d'édition
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'prenom', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login',)}),
    )

    # Champs à afficher dans le formulaire de création
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'nom', 'prenom', 'role', 'password1', 'password2', 'is_staff', 'is_superuser', 'groups')}
        ),
    )

    








@admin.register(Account)
class AccountAdmin(ImportExportModelAdmin):
    resource_class = AccountResource
    list_display = ('reference', 'account_name', 'account_statuts')
    search_fields = ('reference', 'account_name', 'account_statuts')
    list_filter = ('account_statuts',)
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted','reference')


@admin.register(Family)
class FamilyAdmin(ImportExportModelAdmin):
    resource_class = FamilyResource
    list_display = ('reference', 'family_name', 'family_status','get_account_name')
    search_fields = ('reference', 'family_name', 'family_status')
    list_filter = ('family_status',)
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted','reference')
    def get_export_formats(self):
        return [XLSX, CSV]
    
    
    def get_account_name(self, obj):
        return obj.compte.account_name
    get_account_name.short_description = 'Account'


@admin.register(Warehouse)
class WarehouseAdmin(ImportExportModelAdmin):
    resource_class = WarehouseResource
    list_display = ('reference', 'warehouse_name', 'warehouse_type', 'status')
    search_fields = ('reference', 'warehouse_name', 'warehouse_type', 'status')
    list_filter = ('warehouse_type', 'status')
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted','reference')


@admin.register(ZoneType)
class ZoneTypeAdmin(ImportExportModelAdmin):
    resource_class = ZoneTypeResource
    list_display = ('reference', 'type_name', 'status')
    search_fields = ('reference', 'type_name', 'status')
    list_filter = ('status',)
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted','reference')


@admin.register(Zone)
class ZoneAdmin(ImportExportModelAdmin):
    resource_class = ZoneResource
    list_display = ('reference', 'zone_name', 'get_warehouse_name', 'get_zone_type_name', 'zone_status')
    search_fields = ('reference', 'zone_name', 'zone_status')
    list_filter = ('zone_status', 'warehouse_id', 'zone_type_id')
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted')

    def get_warehouse_name(self, obj):
        return obj.warehouse.warehouse_name if obj.warehouse else '-'
    get_warehouse_name.short_description = 'Warehouse'
    get_warehouse_name.admin_order_field = 'warehouse__warehouse_name'

    def get_zone_type_name(self, obj):
        return obj.zone_type.type_name if obj.zone_type else '-'
    get_zone_type_name.short_description = 'Zone Type'
    get_zone_type_name.admin_order_field = 'zone_type__type_name'


@admin.register(SousZone)
class SousZoneAdmin(ImportExportModelAdmin):
    resource_class = SousZoneResource
    list_display = ('reference', 'sous_zone_name', 'get_zone_name', 'sous_zone_status')
    search_fields = ('reference', 'sous_zone_name', 'sous_zone_status')
    list_filter = ('sous_zone_status', 'zone_id')
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted')

    def get_zone_name(self, obj):
        return obj.zone.zone_name if obj.zone else '-'
    get_zone_name.short_description = 'Zone'
    get_zone_name.admin_order_field = 'zone__zone_name'


@admin.register(LocationType)
class LocationTypeAdmin(ImportExportModelAdmin):
    resource_class = LocationTypeResource
    list_display = ('reference', 'name', 'is_active')
    search_fields = ('reference', 'name')
    list_filter = ('is_active',)
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted','reference')


@admin.register(Location)
class LocationAdmin(ImportExportModelAdmin):
    resource_class = LocationResource
    list_display = ('reference', 'get_sous_zone_name', 'get_location_type_name', 'capacity', 'is_active')
    search_fields = ('reference',)
    list_filter = ('sous_zone_id', 'location_type_id', 'is_active')
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted')

    def get_sous_zone_name(self, obj):
        return obj.sous_zone.sous_zone_name if obj.sous_zone else '-'
    get_sous_zone_name.short_description = 'Sous Zone'
    get_sous_zone_name.admin_order_field = 'sous_zone__sous_zone_name'

    def get_location_type_name(self, obj):
        return obj.location_type.name if obj.location_type else '-'
    get_location_type_name.short_description = 'Location Type'
    get_location_type_name.admin_order_field = 'location_type__name'


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            'Short_Description',
            'Barcode',
            'Product_Group',
            'Stock_Unit',
            'Product_Status',
            'Internal_Product_Code',
            'Product_Family',
            'parent_product',
            'Is_Variant',
        )

    def clean(self):
        cleaned_data = super().clean()
        # La validation du champ reference est gérée dans le modèle
        return cleaned_data

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    form = ProductForm
    resource_class = ProductResource
    list_display = ('reference', 'Internal_Product_Code', 'Short_Description', 'Barcode', 'Product_Group', 'Stock_Unit', 'Product_Status','Is_Variant', 'get_family_name')
    list_filter = ('Product_Status', 'Product_Family', 'Is_Variant')
    search_fields = ('reference', 'Short_Description', 'Barcode', 'Internal_Product_Code')
    exclude = ('created_at', 'updated_at', 'deleted_at', 'is_deleted')
    readonly_fields = ('reference',)

    def get_family_name(self, obj):
        return obj.Product_Family.family_name if obj.Product_Family else '-'
    get_family_name.short_description = 'Famille'
    get_family_name.admin_order_field = 'Product_Family__family_name'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Si c'est un nouveau produit
            form.base_fields['reference'] = forms.CharField(required=False, widget=forms.HiddenInput())
        return form


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(ImportExportModelAdmin):
    resource_class = UnitOfMeasureResource
    list_display = ('reference', 'name')
    search_fields = ('reference', 'name')
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted','reference')


@admin.register(Stock)
class StockAdmin(ImportExportModelAdmin):
    resource_class = StockResource
    list_display = (
        'get_location_name',
        'get_product_reference',
        'quantity_available',
        'quantity_reserved',
        'quantity_in_transit',
        'quantity_in_receiving',
        'get_unit_of_measure_name',
    )
    search_fields = (
        'location__location_code',
        'product__reference',
        'product__name',
        'unit_of_measure__name',
    )
    exclude = ('created_at', 'updated_at', 'deleted_at', 'is_deleted')

    def get_location_name(self, obj):
        return obj.location.location_code if obj.location else '-'
    get_location_name.short_description = 'Location'
    get_location_name.admin_order_field = 'location__location_code'

    def get_product_reference(self, obj):
        return obj.product.reference if obj.product else '-'
    get_product_reference.short_description = 'Product Reference'
    get_product_reference.admin_order_field = 'product__reference'

    def get_unit_of_measure_name(self, obj):
        return obj.unit_of_measure.name if obj.unit_of_measure else '-'
    get_unit_of_measure_name.short_description = 'Unit of Measure'
    get_unit_of_measure_name.admin_order_field = 'unit_of_measure__name'