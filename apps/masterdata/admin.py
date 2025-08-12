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
from import_export.widgets import ForeignKeyWidget

from .models import (
    Account, Family, Warehouse, ZoneType, Zone,
    LocationType, Location, Product, UnitOfMeasure,Stock,SousZone,
    Ressource, TypeRessource, RegroupementEmplacement, NSerie
)
from apps.inventory.models import Personne
from django.contrib.auth.admin import UserAdmin
from apps.users.models import UserApp
# ---------------- Resources ---------------- #

class AccountResource(resources.ModelResource):
    account_name = fields.Field(column_name='account_name', attribute='account_name')
    account_statuts = fields.Field(column_name='account_statuts', attribute='account_statuts')

    class Meta:
        model = Account
        fields = ('account_name', 'account_statuts')
        import_id_fields = ('account_name',)






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
    compte = fields.Field(
        column_name='nom de compte',
        attribute='compte',
        widget=ForeignKeyWidget(Account, 'account_name')
    )
    name = fields.Field(
        column_name='nom de famille',
        attribute='family_name'
    )
    statut = fields.Field(
        column_name='statut',
        attribute='family_status'
    )

    class Meta:
        model = Family
        fields = ('name', 'compte', 'statut')
        import_id_fields = ('name',)

class WarehouseResource(resources.ModelResource):
    name = fields.Field(column_name='nom de warehouse', attribute='warehouse_name')
    type = fields.Field(column_name='type', attribute='warehouse_type')
    statut = fields.Field(column_name='statut', attribute='status')
    description = fields.Field(column_name='description', attribute='description')
    adresse = fields.Field(column_name='adresse', attribute='address')
    class Meta:
        model = Warehouse
        fields = ('name', 'type', 'statut', 'description', 'adresse')
        import_id_fields = ('name',)

class ZoneTypeResource(resources.ModelResource):
    name = fields.Field(column_name='nom de type', attribute='type_name')
    statut = fields.Field(column_name='statut', attribute='status')
    description = fields.Field(column_name='description', attribute='description')
    class Meta:
        model = ZoneType
        fields = ('name', 'statut', 'description')
        import_id_fields = ('name',)

class ZoneResource(resources.ModelResource):
    name = fields.Field(column_name='nom de zone', attribute='zone_name')
    statut = fields.Field(column_name='statut', attribute='zone_status')
    description = fields.Field(column_name='description', attribute='description')
    type = fields.Field(column_name='type de zone', attribute='zone_type', widget=ForeignKeyWidget(ZoneType, 'type_name'))
    warehouse = fields.Field(column_name='warehouse', attribute='warehouse', widget=ForeignKeyWidget(Warehouse, 'warehouse_name'))
    class Meta:
        model = Zone
        fields = ('name', 'statut', 'description', 'type', 'warehouse')
        import_id_fields = ('name',)

class SousZoneResource(resources.ModelResource):
    name = fields.Field(column_name='nom de sous-zone', attribute='sous_zone_name')
    statut = fields.Field(column_name='statut', attribute='sous_zone_status')
    description = fields.Field(column_name='description', attribute='description')
    zone = fields.Field(column_name='zone', attribute='zone', widget=ForeignKeyWidget(Zone, 'zone_name'))
    class Meta:
        model = SousZone
        fields = ('name', 'statut', 'description', 'zone')
        import_id_fields = ('name',)

class LocationTypeResource(resources.ModelResource):
    name = fields.Field(column_name='nom de type', attribute='name')
    actif = fields.Field(column_name='actif', attribute='is_active')
    description = fields.Field(column_name='description', attribute='description')
    class Meta:
        model = LocationType
        fields = ('name', 'actif', 'description')
        import_id_fields = ('name',)

class LocationResource(resources.ModelResource):
    location_type = fields.Field(
        column_name='location type',
        attribute='location_type',
        widget=ForeignKeyWidget(LocationType, 'name')
    )
    sous_zone = fields.Field(
        column_name='sous zone',
        attribute='sous_zone',
        widget=ForeignKeyWidget(SousZone, 'sous_zone_name')
    )

    regroupement = fields.Field(
        column_name='regroupement',
        attribute='regroupement',
        widget=ForeignKeyWidget(RegroupementEmplacement, 'nom')
    )

    location_reference = fields.Field(
        column_name='location reference',
        attribute='location_reference'
    )

    class Meta:
        model = Location
        fields = ('location_reference', 'location_type', 'sous_zone', 'regroupement')
        import_id_fields = ('location_reference',)

class ProductResource(resources.ModelResource):
    short_description = fields.Field(column_name='short description', attribute='Short_Description')
    barcode = fields.Field(column_name='barcode', attribute='Barcode')
    product_group = fields.Field(column_name='product group', attribute='Product_Group')
    stock_unit = fields.Field(column_name='stock unit', attribute='Stock_Unit')
    product_status = fields.Field(column_name='product status', attribute='Product_Status')
    internal_product_code = fields.Field(column_name='internal product code', attribute='Internal_Product_Code')
    product_family = fields.Field(column_name='product family', attribute='Product_Family', widget=ForeignKeyWidget(Family, 'family_name'))

    class Meta:
        model = Product
        fields = ('short_description', 'barcode', 'product_group', 'stock_unit', 'product_status', 'internal_product_code', 'product_family')
        import_id_fields = ('barcode',)

class UnitOfMeasureResource(resources.ModelResource):
    name = fields.Field(column_name='nom', attribute='name')
    description = fields.Field(column_name='description', attribute='description')
    class Meta:
        model = UnitOfMeasure
        fields = ('name', 'description')
        import_id_fields = ('name',)

class StockResource(resources.ModelResource):
    reference = fields.Field(column_name='référence', attribute='reference')
    emplacement = fields.Field(column_name='emplacement', attribute='location', widget=ForeignKeyWidget(Location, 'location_reference'))
    article = fields.Field(column_name='article', attribute='product', widget=ForeignKeyWidget(Product, 'reference'))
    quantite = fields.Field(column_name='quantité', attribute='quantity_available')
    reservee = fields.Field(column_name='réservée', attribute='quantity_reserved')
    transit = fields.Field(column_name='transit', attribute='quantity_in_transit')
    reception = fields.Field(column_name='réception', attribute='quantity_in_receiving')
    unite = fields.Field(column_name='unité', attribute='unit_of_measure', widget=ForeignKeyWidget(UnitOfMeasure, 'name'))
    inventaire = fields.Field(column_name='inventaire', attribute='inventory')
    class Meta:
        model = Stock
        fields = ('reference', 'emplacement', 'article', 'quantite', 'reservee', 'transit', 'reception', 'unite', 'inventaire')
        import_id_fields = ('reference',)

class TypeRessourceResource(resources.ModelResource):
    nom = fields.Field(column_name='nom', attribute='libelle')

    class Meta:
        model = TypeRessource
        fields = ('nom',)
        import_id_fields = ('nom',)

class RessourceResource(resources.ModelResource):
    libelle = fields.Field(column_name='libelle', attribute='libelle')
    description = fields.Field(column_name='description', attribute='description')
    status = fields.Field(column_name='status', attribute='status')
    type_ressource = fields.Field(
        column_name='type ressource',
        attribute='type_ressource',
        widget=ForeignKeyWidget(TypeRessource, 'libelle')
    )

    class Meta:
        model = Ressource
        fields = ('libelle', 'description', 'status', 'type_ressource')
        import_id_fields = ('libelle',)

class RegroupementEmplacementResource(resources.ModelResource):
    account = fields.Field(
        column_name='account',
        attribute='account',
        widget=ForeignKeyWidget(Account, 'account_name')
    )
    nom = fields.Field(column_name='nom', attribute='nom')

    class Meta:
        model = RegroupementEmplacement
        import_id_fields = ('nom',)
        fields = ('nom', 'account')


class PersonneResource(resources.ModelResource):
    nom = fields.Field(column_name='nom', attribute='nom')
    prenom = fields.Field(column_name='prenom', attribute='prenom')
    
    class Meta:
        model = Personne
        fields = ('nom', 'prenom')
        import_id_fields = ('nom', 'prenom')
class NSerieResource(resources.ModelResource):
    """
    Resource pour l'import/export des numéros de série
    """
    product = fields.Field(
        column_name='produit',
        attribute='product',
        widget=ForeignKeyWidget(Product, 'Internal_Product_Code')
    )
    n_serie = fields.Field(column_name='numéro de série', attribute='n_serie')
    status = fields.Field(column_name='statut', attribute='status')
    description = fields.Field(column_name='description', attribute='description')
    date_fabrication = fields.Field(column_name='date fabrication', attribute='date_fabrication')
    date_expiration = fields.Field(column_name='date expiration', attribute='date_expiration')
    warranty_end_date = fields.Field(column_name='date fin garantie', attribute='warranty_end_date')

    class Meta:
        model = NSerie
        fields = ('n_serie', 'product', 'status', 'description', 'date_fabrication', 'date_expiration', 'warranty_end_date')
        import_id_fields = ('n_serie', 'product')


# ---------------- Admins ---------------- #



@admin.register(UserApp)
class UserAppAdmin(UserAdmin):
    list_display = ('nom', 'prenom', 'username', 'email', 'type','is_staff', 'is_active','compte')
    list_filter = ('type','is_staff', 'is_active','compte')
    search_fields = ('username', 'email', 'nom', 'prenom','compte')
    ordering = ('username',)

    

    filter_horizontal = ('groups', 'user_permissions')

    # Champs à afficher dans le formulaire d'édition
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'prenom', 'type','compte')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login',)}),
    )

    # Champs à afficher dans le formulaire de création
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'nom', 'prenom', 'type', 'compte', 'password1', 'password2', 'is_staff', 'is_superuser', 'groups')}
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
            'regroupement',
        )

    def clean(self):
        cleaned_data = super().clean()
        # La validation du champ reference est gérée dans le modèle
        return cleaned_data

@admin.register(Location)
class LocationAdmin(ImportExportModelAdmin):
    form = LocationForm
    resource_class = LocationResource
    list_display = ('location_reference', 'get_sous_zone_name', 'get_location_type_name', 'capacity', 'is_active','get_regroupement_name')
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

    def get_regroupement_name(self, obj):
        return obj.regroupement.nom if obj.regroupement else '-'
    get_regroupement_name.short_description = 'Regroupement'
    get_regroupement_name.admin_order_field = 'regroupement__nom'

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
        'get_inventory_reference',  # Ajout de la colonne référence inventaire
    )
    search_fields = (
        'location__location_reference',
        'product__reference',
        'product__name',
        'unit_of_measure__name',
    )
    exclude = ('created_at', 'updated_at', 'deleted_at', 'is_deleted', 'reference')
    readonly_fields = ('reference',)

    def has_import_permission(self, request):
        return False

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

    def get_inventory_reference(self, obj):
        return obj.inventory.reference if obj.inventory else '-'
    get_inventory_reference.short_description = 'Réf. inventaire'

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


@admin.register(NSerie)
class NSerieAdmin(ImportExportModelAdmin):
    resource_class = NSerieResource
    list_display = ('reference', 'n_serie', 'get_product_name', 'status', 'get_product_family', 'date_fabrication', 'date_expiration', 'warranty_end_date', 'is_expired', 'is_warranty_valid')
    list_filter = ('status', 'product__Product_Family', 'date_fabrication', 'date_expiration', 'warranty_end_date')
    search_fields = ('reference', 'n_serie', 'product__Short_Description', 'product__Internal_Product_Code', 'description')
    exclude = ('created_at', 'updated_at', 'deleted_at', 'is_deleted', 'reference')
    readonly_fields = ('reference',)
    date_hierarchy = 'created_at'
    
    def get_product_name(self, obj):
        return obj.product.Short_Description if obj.product else '-'
    get_product_name.short_description = 'Produit'
    get_product_name.admin_order_field = 'product__Short_Description'
    
    def get_product_family(self, obj):
        return obj.product.Product_Family.family_name if obj.product and obj.product.Product_Family else '-'
    get_product_family.short_description = 'Famille'
    get_product_family.admin_order_field = 'product__Product_Family__family_name'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Si c'est un nouveau numéro de série
            form.base_fields['reference'] = forms.CharField(required=False, widget=forms.HiddenInput())
        return form


@admin.register(RegroupementEmplacement)
class RegroupementEmplacementAdmin(ImportExportModelAdmin):
    resource_class = RegroupementEmplacementResource
    list_display = ('nom', 'account')
    search_fields = ('nom', 'account__account_name')


@admin.register(Personne)
class PersonneAdmin(ImportExportModelAdmin):
    resource_class = PersonneResource
    list_display = ('reference', 'nom', 'prenom')
    search_fields = ('reference', 'nom', 'prenom')
    exclude = ('created_at', 'updated_at', 'deleted_at', 'is_deleted', 'reference')
    readonly_fields = ('reference',)












