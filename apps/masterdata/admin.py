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
    LocationType, Location, Product, UnitOfMeasure,Stock,SousZone,
    Ressource, TypeRessource
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

    def dehydrate_compte(self, obj):
        """Convertit l'objet Account en nom pour l'exportation"""
        return obj.compte.account_name if obj.compte else ''

    def before_import_row(self, row, **kwargs):
        # Valider le statut de famille
        family_status = row.get('family status')
        if family_status:
            valid_statuses = ['ACTIVE', 'INACTIVE', 'OBSOLETE']
            if family_status.upper() not in valid_statuses:
                raise ValueError(f"Le statut '{family_status}' n'est pas valide. Les valeurs autorisées sont : {', '.join(valid_statuses)}")
            # Normaliser le statut en majuscules
            row['family status'] = family_status.upper()
        
        # Chercher l'objet account à partir du nom dans la ligne d'importation
        account_name = row.get('account')
        if account_name:
            try:
                if str(account_name).isdigit():
                    account_obj = Account.objects.get(id=account_name)
                else:
                    account_obj = Account.objects.get(account_name=account_name)
                row['account'] = account_obj.id
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
        widget=widgets.IntegerWidget()
    )
    warehouse_id = fields.Field(
        column_name='werhouse',
        attribute='warehouse_id',
        widget=widgets.IntegerWidget()
    )

    class Meta:
        model = Zone  # À corriger si c'est censé être Zone et non Family
        fields = ('zone_name', 'zone_status','description','zone_type_id','warehouse_id')
        exclude = ('id', 'reference')
        import_id_fields = ()

    def dehydrate_zone_type_id(self, obj):
        """Convertit l'objet ZoneType en nom pour l'exportation"""
        return obj.zone_type.type_name if obj.zone_type else ''

    def dehydrate_warehouse_id(self, obj):
        """Convertit l'objet Warehouse en nom pour l'exportation"""
        return obj.warehouse.warehouse_name if obj.warehouse else ''

    def before_import_row(self, row, **kwargs):
        # Valider le statut de zone
        zone_status = row.get('zone status')
        if zone_status:
            valid_statuses = ['ACTIVE', 'INACTIVE', 'BLOCKED']
            if zone_status.upper() not in valid_statuses:
                raise ValueError(f"Le statut '{zone_status}' n'est pas valide. Les valeurs autorisées sont : {', '.join(valid_statuses)}")
            # Normaliser le statut en majuscules
            row['zone status'] = zone_status.upper()
        
        zone_type_value = row.get('zone type')
        warehouse_value = row.get('werhouse')  # attention ici

        if zone_type_value:
            # Essayer d'abord par ID, puis par nom
            try:
                if str(zone_type_value).isdigit():
                    zone_type_obj = ZoneType.objects.get(id=zone_type_value)
                else:
                    zone_type_obj = ZoneType.objects.get(type_name=zone_type_value)
                row['zone type'] = zone_type_obj.id
            except ZoneType.DoesNotExist:
                raise ValueError(f"Le type de zone '{zone_type_value}' n'existe pas dans la base de données.")

        if warehouse_value:
            # Essayer d'abord par ID, puis par nom
            try:
                if str(warehouse_value).isdigit():
                    warehouse_obj = Warehouse.objects.get(id=warehouse_value)
                else:
                    warehouse_obj = Warehouse.objects.get(warehouse_name=warehouse_value)
                row['werhouse'] = warehouse_obj.id
            except Warehouse.DoesNotExist:
                raise ValueError(f"L'entrepôt '{warehouse_value}' n'existe pas dans la base de données.")


    



class SousZoneResource(resources.ModelResource):
    sous_zone_name = fields.Field(column_name='sous zone name', attribute='sous_zone_name', widget=widgets.CharWidget())
    sous_zone_status = fields.Field(column_name='sous zone status', attribute='sous_zone_status', widget=widgets.CharWidget())
    description = fields.Field(column_name='description', attribute='description', widget=widgets.CharWidget())
    zone_id = fields.Field(
        column_name='zone',
        attribute='zone_id',
        widget=widgets.IntegerWidget()
    )
    
    class Meta:
        model = SousZone  # À corriger si c'est censé être Zone et non Family
        fields = ('sous_zone_name', 'sous_zone_status','description','zone_id')
        exclude = ('id', 'reference')
        import_id_fields = ()

    def dehydrate_zone_id(self, obj):
        """Convertit l'objet Zone en nom pour l'exportation"""
        return obj.zone.zone_name if obj.zone else ''

    def before_import_row(self, row, **kwargs):
        # Valider le statut de sous-zone
        sous_zone_status = row.get('sous zone status')
        if sous_zone_status:
            valid_statuses = ['ACTIVE', 'INACTIVE', 'BLOCKED']
            if sous_zone_status.upper() not in valid_statuses:
                raise ValueError(f"Le statut '{sous_zone_status}' n'est pas valide. Les valeurs autorisées sont : {', '.join(valid_statuses)}")
            # Normaliser le statut en majuscules
            row['sous zone status'] = sous_zone_status.upper()
        
        zone_value = row.get('zone')

        if zone_value:
            # Essayer d'abord par ID, puis par nom
            try:
                if str(zone_value).isdigit():
                    zone_obj = Zone.objects.get(id=zone_value)
                else:
                    zone_obj = Zone.objects.get(zone_name=zone_value)
                row['zone'] = zone_obj.id
            except Zone.DoesNotExist:
                raise ValueError(f"La zone '{zone_value}' n'existe pas dans la base de données.")

        



    
    
    
    

class LocationTypeResource(resources.ModelResource):
    class Meta:
        model = LocationType

class LocationResource(resources.ModelResource):
    location_reference = fields.Field(column_name='location reference', attribute='location_reference', widget=widgets.CharWidget())
    capacity = fields.Field(column_name='capacity', attribute='capacity', widget=widgets.CharWidget())
    is_active = fields.Field(column_name='active', attribute='is_active', widget=widgets.CharWidget())
    description = fields.Field(column_name='description', attribute='description', widget=widgets.CharWidget())
    location_type_id = fields.Field(
            column_name='location type',
            attribute='location_type_id',
            widget=widgets.IntegerWidget()
        )
    sous_zone_id = fields.Field(
        column_name='sous zone',
        attribute='sous_zone_id',
        widget=widgets.IntegerWidget()
    )
    class Meta:
        model = Location
        fields = ('location_reference', 'capacity', 'is_active','description','location_type_id','sous_zone_id')
        exclude = ('id', 'reference')
        import_id_fields = ('location_reference',)
        skip_unchanged = True
        report_skipped = True

    def dehydrate_location_type_id(self, obj):
        """Convertit l'objet LocationType en nom pour l'exportation"""
        return obj.location_type.name if obj.location_type else ''

    def dehydrate_sous_zone_id(self, obj):
        """Convertit l'objet SousZone en nom pour l'exportation"""
        return obj.sous_zone.sous_zone_name if obj.sous_zone else ''

    def before_import_row(self, row, **kwargs):
        # Récupérer les objets et les assigner à la ligne
        location_type_value = row.get('location type')
        sous_zone_value = row.get('sous zone')

        if location_type_value:
            # Essayer d'abord par ID, puis par nom
            try:
                if str(location_type_value).isdigit():
                    location_type_obj = LocationType.objects.get(id=location_type_value)
                else:
                    location_type_obj = LocationType.objects.get(name=location_type_value)
                row['location type'] = location_type_obj.id
            except LocationType.DoesNotExist:
                raise ValueError(f"Le type de location '{location_type_value}' n'existe pas dans la base de données.")

        if sous_zone_value:
            # Essayer d'abord par ID, puis par nom
            try:
                if str(sous_zone_value).isdigit():
                    sous_zone_obj = SousZone.objects.get(id=sous_zone_value)
                else:
                    sous_zone_obj = SousZone.objects.get(sous_zone_name=sous_zone_value)
                row['sous zone'] = sous_zone_obj.id
            except SousZone.DoesNotExist:
                raise ValueError(f"La sous zone '{sous_zone_value}' n'existe pas dans la base de données.")

    def save_instance(self, instance, is_create, row, **kwargs):
        """Surcharge pour gérer les conflits de clés dupliquées"""
        try:
            super().save_instance(instance, is_create, row, **kwargs)
        except Exception as e:
            if "masterdata_location_reference_key" in str(e):
                # Si c'est un conflit de référence, essayer de mettre à jour l'instance existante
                try:
                    existing_location = Location.objects.get(location_reference=instance.location_reference)
                    # Mettre à jour les champs de l'instance existante
                    for field in ['capacity', 'is_active', 'description', 'location_type_id', 'sous_zone_id']:
                        if hasattr(instance, field):
                            setattr(existing_location, field, getattr(instance, field))
                    existing_location.save()
                    return existing_location
                except Location.DoesNotExist:
                    pass
            raise e
        









        

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
        widget=widgets.IntegerWidget()
    )

    parent_product = fields.Field(
        column_name='parent product',
        attribute='parent_product',
        widget=widgets.IntegerWidget()
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

    def dehydrate_Product_Family(self, obj):
        """Convertit l'objet Family en nom pour l'exportation"""
        return obj.Product_Family.family_name if obj.Product_Family else ''

    def dehydrate_parent_product(self, obj):
        """Convertit l'objet Product parent en référence pour l'exportation"""
        return obj.parent_product.reference if obj.parent_product else ''

    def before_import_row(self, row, **kwargs):
        # Valider le statut de produit
        product_status = row.get('product status')
        if product_status:
            valid_statuses = ['ACTIVE', 'INACTIVE', 'OBSOLETE']
            if product_status.upper() not in valid_statuses:
                raise ValueError(f"Le statut '{product_status}' n'est pas valide. Les valeurs autorisées sont : {', '.join(valid_statuses)}")
            # Normaliser le statut en majuscules
            row['product status'] = product_status.upper()
        
        # Vérifier si la famille existe et l'assigner
        family_value = row.get('product family')
        if family_value:
            try:
                if str(family_value).isdigit():
                    family_obj = Family.objects.get(id=family_value)
                else:
                    family_obj = Family.objects.get(family_name=family_value)
                row['product family'] = family_obj.id
            except Family.DoesNotExist:
                raise ValueError(f"La famille de produit '{family_value}' n'existe pas.")

        # Vérifier si le produit parent existe et l'assigner
        parent_value = row.get('parent product')
        if parent_value:
            try:
                if str(parent_value).isdigit():
                    parent_obj = Product.objects.get(id=parent_value)
                else:
                    parent_obj = Product.objects.get(reference=parent_value)
                row['parent product'] = parent_obj.id
            except Product.DoesNotExist:
                raise ValueError(f"Le produit parent '{parent_value}' n'existe pas.")

class UnitOfMeasureResource(resources.ModelResource):
    class Meta:
        model = UnitOfMeasure


class StockResource(resources.ModelResource):
    location = fields.Field(
        column_name='location',
        attribute='location',
        widget=widgets.IntegerWidget()
    )
    product = fields.Field(
        column_name='product',
        attribute='product',
        widget=widgets.IntegerWidget()
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
        widget=widgets.IntegerWidget()
    )
    inventory = fields.Field(
        column_name='inventory',
        attribute='inventory',
        widget=widgets.IntegerWidget()
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
            'inventory',
        )
        exclude = ('id', 'reference')
        import_id_fields = ('location', 'product')

    def dehydrate_location(self, obj):
        """Convertit l'objet Location en référence pour l'exportation"""
        return obj.location.location_reference if obj.location else ''

    def dehydrate_product(self, obj):
        """Convertit l'objet Product en référence pour l'exportation"""
        return obj.product.reference if obj.product else ''

    def dehydrate_unit_of_measure(self, obj):
        """Convertit l'objet UnitOfMeasure en nom pour l'exportation"""
        return obj.unit_of_measure.name if obj.unit_of_measure else ''

    def dehydrate_inventory(self, obj):
        """Convertit l'objet Inventory en ID pour l'exportation"""
        return obj.inventory.id if obj.inventory else ''

    def before_import_row(self, row, **kwargs):
        # Vérifie que la location existe et l'assigner
        location_value = row.get('location')
        if location_value:
            try:
                if str(location_value).isdigit():
                    location_obj = Location.objects.get(id=location_value)
                else:
                    location_obj = Location.objects.get(location_reference=location_value)
                row['location'] = location_obj.id
            except Location.DoesNotExist:
                raise ValueError(f"La location '{location_value}' n'existe pas dans la base de données.")

        # Vérifie que le produit existe et l'assigner
        product_value = row.get('product')
        if product_value:
            try:
                if str(product_value).isdigit():
                    product_obj = Product.objects.get(id=product_value)
                else:
                    product_obj = Product.objects.get(reference=product_value)
                row['product'] = product_obj.id
            except Product.DoesNotExist:
                raise ValueError(f"Le produit '{product_value}' n'existe pas dans la base de données.")

        # Vérifie que l'unité de mesure existe et l'assigner
        unit_value = row.get('unit of measure')
        if unit_value:
            try:
                if str(unit_value).isdigit():
                    unit_obj = UnitOfMeasure.objects.get(id=unit_value)
                else:
                    unit_obj = UnitOfMeasure.objects.get(name=unit_value)
                row['unit of measure'] = unit_obj.id
            except UnitOfMeasure.DoesNotExist:
                raise ValueError(f"L'unité de mesure '{unit_value}' n'existe pas dans la base de données.")

        # Vérifie que l'inventory existe et l'assigner, ou créer un inventory par défaut
        inventory_value = row.get('inventory')
        if inventory_value:
            try:
                from apps.inventory.models import Inventory
                if str(inventory_value).isdigit():
                    inventory_obj = Inventory.objects.get(id=inventory_value)
                else:
                    # Si ce n'est pas un ID, chercher par référence
                    inventory_obj = Inventory.objects.get(reference=inventory_value)
                row['inventory'] = inventory_obj.id
            except Exception:
                raise ValueError(f"L'inventory '{inventory_value}' n'existe pas dans la base de données.")
        else:
            # Créer un inventory par défaut si aucun n'est fourni
            try:
                from apps.inventory.models import Inventory
                from django.utils import timezone
                
                # Chercher un inventory par défaut ou en créer un
                default_inventory = Inventory.objects.filter(
                    status='EN PREPARATION',
                    inventory_type='GENERAL'
                ).first()
                
                if not default_inventory:
                    # Créer un nouvel inventory par défaut
                    default_inventory = Inventory.objects.create(
                        label='Inventory par défaut - Import Stock',
                        date=timezone.now(),
                        status='EN PREPARATION',
                        inventory_type='GENERAL'
                    )
                
                row['inventory'] = default_inventory.id
            except Exception as e:
                raise ValueError(f"Impossible de créer ou récupérer un inventory par défaut: {str(e)}")


class TypeRessourceResource(resources.ModelResource):
    libelle = fields.Field(column_name='libelle', attribute='libelle', widget=widgets.CharWidget())
    description = fields.Field(column_name='description', attribute='description', widget=widgets.CharWidget())
    
    class Meta:
        model = TypeRessource
        fields = ('libelle', 'description')
        exclude = ('id', 'reference', 'created_at', 'updated_at', 'deleted_at', 'is_deleted')
        import_id_fields = ()


class RessourceResource(resources.ModelResource):
    libelle = fields.Field(column_name='libelle', attribute='libelle', widget=widgets.CharWidget())
    description = fields.Field(column_name='description', attribute='description', widget=widgets.CharWidget())
    status = fields.Field(column_name='status', attribute='status', widget=widgets.CharWidget())
    type_ressource = fields.Field(
        column_name='type ressource',
        attribute='type_ressource',
        widget=widgets.ForeignKeyWidget(TypeRessource, 'libelle')
    )
    
    class Meta:
        model = Ressource
        fields = ('libelle', 'description', 'status', 'type_ressource')
        exclude = ('id', 'reference', 'created_at', 'updated_at', 'deleted_at', 'is_deleted')
        import_id_fields = ()

    def dehydrate_type_ressource(self, obj):
        """Convertit l'objet TypeRessource en libellé pour l'exportation"""
        return obj.type_ressource.libelle if obj.type_ressource else ''

    def before_import_row(self, row, **kwargs):
        # Vérifier que le statut est valide
        status = row.get('status')
        if status and status not in ['ACTIVE', 'INACTIVE']:
            raise ValueError(f"Le statut '{status}' n'est pas valide. Les valeurs autorisées sont 'ACTIVE' et 'INACTIVE'.")
        
        # Vérifier que le type de ressource existe et l'assigner
        type_ressource_value = row.get('type ressource')
        if type_ressource_value:
            try:
                if str(type_ressource_value).isdigit():
                    type_ressource_obj = TypeRessource.objects.get(id=type_ressource_value)
                else:
                    type_ressource_obj = TypeRessource.objects.get(libelle=type_ressource_value)
                row['type ressource'] = type_ressource_obj.id
            except TypeRessource.DoesNotExist:
                raise ValueError(f"Le type de ressource '{type_ressource_value}' n'existe pas dans la base de données.")


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












