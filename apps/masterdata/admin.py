from django.contrib import admin
from django import forms
from django.utils import timezone
import random
import hashlib
import uuid
from datetime import datetime

# Register your models here.
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields, widgets
from import_export.formats.base_formats import XLSX, CSV, XLS

from .models import (
    Account, Family, Warehouse, ZoneType, Zone,
    LocationType, Location, Product, UnitOfMeasure,Stock,SousZone,
    Ressource, TypeRessource
)
from django.contrib.auth.admin import UserAdmin
from apps.users.models import UserApp
# ---------------- Resources ---------------- #

class AccountResource(resources.ModelResource):
    class Meta:
        model = Account






class AutoCreateAccountWidget(widgets.ForeignKeyWidget):
    """Widget personnalisé qui crée automatiquement les comptes manquants"""
    
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        
        try:
            # Essayer d'abord par ID
            if str(value).isdigit():
                return Account.objects.get(id=value)
            # Puis par nom
            return Account.objects.get(account_name=value)
        except Account.DoesNotExist:
            # Créer automatiquement l'Account s'il n'existe pas
            try:
                # Générer une référence unique pour le compte
                timestamp = int(timezone.now().timestamp())
                timestamp_short = str(timestamp)[-4:]
                data_to_hash = f"{value}{timestamp}"
                hash_value = hashlib.md5(data_to_hash.encode()).hexdigest()[:4].upper()
                reference = f"ACC-{timestamp_short}-{hash_value}"
                
                # S'assurer que la référence ne dépasse pas 20 caractères
                if len(reference) > 20:
                    reference = reference[:20]
                
                # Créer le nouveau compte
                account_obj = Account.objects.create(
                    reference=reference,
                    account_name=value,
                    account_statuts='ACTIVE',  # Statut par défaut
                    description=f"Compte créé automatiquement lors de l'import de famille: {value}"
                )
                return account_obj
            except Exception as e:
                raise ValueError(f"Impossible de créer le compte '{value}': {str(e)}")

class FamilyLookupWidget(widgets.ForeignKeyWidget):
    """Widget personnalisé pour rechercher les familles par ID ou nom"""
    
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        
        try:
            # Essayer d'abord par ID
            if str(value).isdigit():
                return Family.objects.get(id=value)
            # Puis par nom
            return Family.objects.get(family_name=value)
        except Family.DoesNotExist:
            raise ValueError(f"La famille '{value}' n'existe pas dans la base de données.")

class ProductLookupWidget(widgets.ForeignKeyWidget):
    """Widget personnalisé pour rechercher les produits par ID ou référence"""
    
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        
        try:
            # Essayer d'abord par ID
            if str(value).isdigit():
                return Product.objects.get(id=value)
            # Puis par référence
            return Product.objects.get(reference=value)
        except Product.DoesNotExist:
            raise ValueError(f"Le produit '{value}' n'existe pas dans la base de données.")

class StockUnitWidget(widgets.CharWidget):
    """Widget personnalisé pour l'unité de stock qui tronque à 3 caractères"""
    
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        
        # Tronquer à 3 caractères maximum
        return str(value)[:3].upper()

class FamilyResource(resources.ModelResource):
    compte_name = fields.Field(column_name='compte', attribute='compte', widget=widgets.CharWidget())
    class Meta:
        model = Family
        fields = ('family_name', 'family_status', 'family_description', 'compte_name')

class WarehouseResource(resources.ModelResource):
    class Meta:
        model = Warehouse

class ZoneTypeResource(resources.ModelResource):
    class Meta:
        model = ZoneType

class ZoneResource(resources.ModelResource):
    zone_type_name = fields.Field(column_name='zone_type', attribute='zone_type', widget=widgets.CharWidget())
    warehouse_name = fields.Field(column_name='warehouse', attribute='warehouse', widget=widgets.CharWidget())
    class Meta:
        model = Zone
        fields = ('zone_name', 'zone_status', 'description', 'zone_type_name', 'warehouse_name')

class SousZoneResource(resources.ModelResource):
    zone_name = fields.Field(column_name='zone', attribute='zone', widget=widgets.CharWidget())
    class Meta:
        model = SousZone
        fields = ('sous_zone_name', 'sous_zone_status', 'description', 'zone_name')

class LocationTypeResource(resources.ModelResource):
    class Meta:
        model = LocationType

class LocationResource(resources.ModelResource):
    location_type_name = fields.Field(column_name='location_type', attribute='location_type', widget=widgets.CharWidget())
    sous_zone_name = fields.Field(column_name='sous_zone', attribute='sous_zone', widget=widgets.CharWidget())
    class Meta:
        model = Location
        fields = ('location_reference', 'capacity', 'is_active', 'description', 'location_type_name', 'sous_zone_name')

class ProductResource(resources.ModelResource):
    product_family_name = fields.Field(column_name='product_family', attribute='Product_Family', widget=widgets.CharWidget())
    parent_product_reference = fields.Field(column_name='parent_product', attribute='parent_product', widget=widgets.CharWidget())
    class Meta:
        model = Product
        fields = ('reference', 'Short_Description', 'Barcode', 'Product_Group', 'Stock_Unit', 'Product_Status', 'Internal_Product_Code', 'product_family_name', 'parent_product_reference', 'Is_Variant')

class UnitOfMeasureResource(resources.ModelResource):
    class Meta:
        model = UnitOfMeasure

class StockResource(resources.ModelResource):
    location_reference = fields.Field(column_name='location', attribute='location', widget=widgets.CharWidget())
    product_reference = fields.Field(column_name='product', attribute='product', widget=widgets.CharWidget())
    unit_of_measure_name = fields.Field(column_name='unit_of_measure', attribute='unit_of_measure', widget=widgets.CharWidget())
    class Meta:
        model = Stock
        fields = ('location_reference', 'product_reference', 'quantity_available', 'quantity_reserved', 'quantity_in_transit', 'quantity_in_receiving', 'unit_of_measure_name', 'inventory')

class TypeRessourceResource(resources.ModelResource):
    class Meta:
        model = TypeRessource

class RessourceResource(resources.ModelResource):
    type_ressource_libelle = fields.Field(column_name='type_ressource', attribute='type_ressource', widget=widgets.CharWidget())
    class Meta:
        model = Ressource
        fields = ('libelle', 'description', 'status', 'type_ressource_libelle')


# ---------------- Admins ---------------- #



@admin.register(UserApp)
class UserAppAdmin(UserAdmin):
    list_display = ('nom', 'prenom', 'username', 'email', 'type','is_staff', 'is_active')
    list_filter = ('type','is_staff', 'is_active')
    search_fields = ('username', 'email', 'nom', 'prenom')
    ordering = ('username',)

    

    filter_horizontal = ('groups', 'user_permissions')

    # Champs à afficher dans le formulaire d'édition
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'prenom', 'type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login',)}),
    )

    # Champs à afficher dans le formulaire de création
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'nom', 'prenom', 'type', 'password1', 'password2', 'is_staff', 'is_superuser', 'groups')}
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


class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = (
            'warehouse',
            'zone_name',
            'zone_type',
            'description',
            'zone_status',
        )

    def clean(self):
        cleaned_data = super().clean()
        # La validation du champ reference est gérée dans le modèle
        return cleaned_data

@admin.register(Zone)
class ZoneAdmin(ImportExportModelAdmin):
    form = ZoneForm
    resource_class = ZoneResource
    list_display = ('reference', 'zone_name', 'get_warehouse_name', 'get_zone_type_name', 'zone_status')
    search_fields = ('reference', 'zone_name', 'zone_status')
    list_filter = ('zone_status', 'warehouse_id', 'zone_type_id')
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted','reference')
    readonly_fields = ('reference',)

    def get_warehouse_name(self, obj):
        return obj.warehouse.warehouse_name if obj.warehouse else '-'
    get_warehouse_name.short_description = 'Warehouse'
    get_warehouse_name.admin_order_field = 'warehouse__warehouse_name'

    def get_zone_type_name(self, obj):
        return obj.zone_type.type_name if obj.zone_type else '-'
    get_zone_type_name.short_description = 'Zone Type'
    get_zone_type_name.admin_order_field = 'zone_type__type_name'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Si c'est une nouvelle zone
            form.base_fields['reference'] = forms.CharField(required=False, widget=forms.HiddenInput())
        return form


class SousZoneForm(forms.ModelForm):
    class Meta:
        model = SousZone
        fields = (
            'zone',
            'sous_zone_name',
            'description',
            'sous_zone_status',
        )

    def clean(self):
        cleaned_data = super().clean()
        # La validation du champ reference est gérée dans le modèle
        return cleaned_data

@admin.register(SousZone)
class SousZoneAdmin(ImportExportModelAdmin):
    form = SousZoneForm
    resource_class = SousZoneResource
    list_display = ('reference', 'sous_zone_name', 'get_zone_name', 'sous_zone_status')
    search_fields = ('reference', 'sous_zone_name', 'sous_zone_status')
    list_filter = ('sous_zone_status', 'zone_id')
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted','reference')
    readonly_fields = ('reference',)

    def get_zone_name(self, obj):
        return obj.zone.zone_name if obj.zone else '-'
    get_zone_name.short_description = 'Zone'
    get_zone_name.admin_order_field = 'zone__zone_name'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Si c'est une nouvelle sous-zone
            form.base_fields['reference'] = forms.CharField(required=False, widget=forms.HiddenInput())
        return form


@admin.register(LocationType)
class LocationTypeAdmin(ImportExportModelAdmin):
    resource_class = LocationTypeResource
    list_display = ('reference', 'name', 'is_active')
    search_fields = ('reference', 'name')
    list_filter = ('is_active',)
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted','reference')


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = (
            'sous_zone',
            'location_type',
            'location_reference',
            'capacity',
            'is_active',
            'description',
        )

    def clean(self):
        cleaned_data = super().clean()
        # La validation du champ reference est gérée dans le modèle
        return cleaned_data

@admin.register(Location)
class LocationAdmin(ImportExportModelAdmin):
    form = LocationForm
    resource_class = LocationResource
    list_display = ('location_reference', 'get_sous_zone_name', 'get_location_type_name', 'capacity', 'is_active')
    search_fields = ('location_reference',)
    list_filter = ('sous_zone_id', 'location_type_id', 'is_active')
    exclude = ('created_at', 'updated_at', 'deleted_at','is_deleted','reference')
    readonly_fields = ('reference',)

    def get_sous_zone_name(self, obj):
        return obj.sous_zone.sous_zone_name if obj.sous_zone else '-'
    get_sous_zone_name.short_description = 'Sous Zone'
    get_sous_zone_name.admin_order_field = 'sous_zone__sous_zone_name'

    def get_location_type_name(self, obj):
        return obj.location_type.name if obj.location_type else '-'
    get_location_type_name.short_description = 'Location Type'
    get_location_type_name.admin_order_field = 'location_type__name'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Si c'est un nouvel emplacement
            form.base_fields['reference'] = forms.CharField(required=False, widget=forms.HiddenInput())
        return form


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            'Internal_Product_Code',
            'Short_Description',
            'Barcode',
            'Product_Group',
            'Stock_Unit',
            'Product_Status',          
            'Product_Family',
            'Is_Variant',
            'parent_product',   
            'n_lot',
            'n_serie',
            'dlc',
        )

    def clean(self):
        cleaned_data = super().clean()
        # La validation du champ reference est gérée dans le modèle
        return cleaned_data

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    form = ProductForm
    resource_class = ProductResource
    list_display = ('reference', 'Internal_Product_Code', 'Short_Description', 'Barcode', 'Product_Group', 'Stock_Unit', 'Product_Status','Is_Variant', 'get_family_name','n_lot','n_serie','dlc')
    list_filter = ('Product_Status', 'Product_Family', 'Is_Variant','n_lot','n_serie','dlc')
    search_fields = ('reference', 'Short_Description', 'Barcode', 'Internal_Product_Code','n_lot','n_serie','dlc')
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


class StockForm(forms.ModelForm):
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
            'inventory',
        )

    def clean(self):
        cleaned_data = super().clean()
        # La validation du champ reference est gérée dans le modèle
        return cleaned_data

@admin.register(Stock)
class StockAdmin(ImportExportModelAdmin):
    form = StockForm
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
        'location__location_reference',
        'product__reference',
        'product__name',
        'unit_of_measure__name',
    )
    exclude = ('created_at', 'updated_at', 'deleted_at', 'is_deleted', 'reference')
    readonly_fields = ('reference',)

    def get_location_name(self, obj):
        return obj.location.location_reference if obj.location else '-'
    get_location_name.short_description = 'Location'
    get_location_name.admin_order_field = 'location__location_reference'

    def get_product_reference(self, obj):
        return obj.product.reference if obj.product else '-'
    get_product_reference.short_description = 'Product Reference'
    get_product_reference.admin_order_field = 'product__reference'

    def get_unit_of_measure_name(self, obj):
        return obj.unit_of_measure.name if obj.unit_of_measure else '-'
    get_unit_of_measure_name.short_description = 'Unit of Measure'
    get_unit_of_measure_name.admin_order_field = 'unit_of_measure__name'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Si c'est un nouveau stock
            form.base_fields['reference'] = forms.CharField(required=False, widget=forms.HiddenInput())
        return form


@admin.register(TypeRessource)
class TypeRessourceAdmin(ImportExportModelAdmin):
    resource_class = TypeRessourceResource
    list_display = ('reference', 'libelle', 'description')
    search_fields = ('reference', 'libelle', 'description')
    exclude = ('created_at', 'updated_at', 'deleted_at', 'is_deleted', 'reference')


@admin.register(Ressource)
class RessourceAdmin(ImportExportModelAdmin):
    resource_class = RessourceResource
    list_display = ('reference', 'libelle', 'get_type_ressource', 'status', 'description')
    search_fields = ('reference', 'libelle', 'description', 'type_ressource__libelle')
    list_filter = ('status', 'type_ressource')
    exclude = ('created_at', 'updated_at', 'deleted_at', 'is_deleted', 'reference')
    
    def get_type_ressource(self, obj):
        return obj.type_ressource.libelle if obj.type_ressource else '-'
    get_type_ressource.short_description = 'Type de ressource'
    get_type_ressource.admin_order_field = 'type_ressource__libelle'












