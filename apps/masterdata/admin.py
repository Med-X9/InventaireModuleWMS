from django.contrib import admin
from django import forms
from django.utils import timezone
import random
import hashlib
import uuid
from datetime import datetime
import os

# Register your models here.
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields, widgets
from import_export.formats.base_formats import XLSX, CSV, XLS
from import_export.widgets import ForeignKeyWidget
from django.db import transaction

from .models import (
    Account, Family, Warehouse, ZoneType, Zone,
    LocationType, Location, Product, UnitOfMeasure,Stock,SousZone,
    Ressource, TypeRessource, RegroupementEmplacement, NSerie,
    ImportTask, ImportError
)
from apps.inventory.models import Personne
from django.contrib.auth.admin import UserAdmin
from apps.users.models import UserApp
from apps.inventory.models import Personne
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

class OptionalBooleanWidget(widgets.BooleanWidget):
    """Widget booléen personnalisé qui gère les valeurs vides/optionnelles"""
    
    def clean(self, value, row=None, *args, **kwargs):
        """
        Nettoie la valeur booléenne.
        Les valeurs vides, None, ou chaînes vides retournent False (valeur par défaut).
        """
        if value is None or value == '' or str(value).strip() == '':
            return False
        return super().clean(value, row, *args, **kwargs)

class AutoCreateRegroupementWidget(widgets.ForeignKeyWidget):
    """Widget personnalisé qui crée automatiquement les regroupements manquants"""
    
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        
        try:
            # Essayer d'abord de trouver le regroupement existant
            return RegroupementEmplacement.objects.get(nom=value)
        except RegroupementEmplacement.DoesNotExist:
            # Créer automatiquement le regroupement s'il n'existe pas
            try:
                # Essayer de trouver l'account à partir de la ligne ou utiliser un account par défaut
                account = None
                
                # Option 1: Chercher un account dans la ligne d'import
                if row:
                    # Chercher un champ account dans la ligne
                    account_name = row.get('account', row.get('nom de compte', ''))
                    if account_name:
                        try:
                            account = Account.objects.get(account_name=account_name)
                        except Account.DoesNotExist:
                            pass
                
                # Option 2: Si pas d'account dans la ligne, chercher via la sous_zone
                if not account and row:
                    sous_zone_name = row.get('sous zone', '')
                    if sous_zone_name:
                        try:
                            from .models import SousZone
                            sous_zone = SousZone.objects.get(sous_zone_name=sous_zone_name)
                            # Essayer de trouver l'account via la zone -> warehouse
                            if hasattr(sous_zone, 'zone') and sous_zone.zone:
                                zone = sous_zone.zone
                                if hasattr(zone, 'warehouse') and zone.warehouse:
                                    warehouse = zone.warehouse
                                    # Si le warehouse a un account, l'utiliser
                                    if hasattr(warehouse, 'account'):
                                        account = warehouse.account
                        except Exception:
                            pass
                
                # Option 3: Utiliser le premier account disponible comme fallback
                if not account:
                    account = Account.objects.first()
                    if not account:
                        raise ValueError("Aucun compte disponible pour créer le regroupement. Veuillez créer un compte d'abord.")
                
                # Vérifier si l'account a déjà un regroupement (OneToOneField)
                if hasattr(account, 'regroupement_emplacement'):
                    # Si l'account a déjà un regroupement, le retourner
                    # (même si le nom est différent, car c'est une contrainte OneToOneField)
                    return account.regroupement_emplacement
                
                # Vérifier si un regroupement avec ce nom existe déjà pour un autre account
                existing_regroupement = RegroupementEmplacement.objects.filter(nom=value).first()
                if existing_regroupement:
                    # Si un regroupement avec ce nom existe déjà, le retourner
                    return existing_regroupement
                
                # Créer le nouveau regroupement pour l'account
                regroupement = RegroupementEmplacement.objects.create(
                    account=account,
                    nom=value
                )
                return regroupement
            except Exception as e:
                raise ValueError(f"Impossible de créer le regroupement '{value}': {str(e)}")

class FamilyResource(resources.ModelResource):
    compte = fields.Field(
        column_name='nom de compte',
        attribute='compte',
        widget=AutoCreateAccountWidget(Account, 'account_name')
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
    
    def _check_import_id_fields(self, headers):
        """
        Surcharge pour mapper les noms de champs aux column_name.
        Permet d'utiliser 'nom de famille' dans le fichier d'import
        alors que le champ s'appelle 'name' dans la ressource.
        Gère aussi les variations de casse et d'espaces.
        """
        # Mapping des noms de champs vers les column_name
        field_to_column = {
            'name': 'nom de famille',
        }
        
        # Vérifier que les column_name correspondants sont présents dans les en-têtes
        missing_fields = []
        for field_name in self.get_import_id_fields():
            column_name = field_to_column.get(field_name, field_name)
            # Vérifier aussi avec différentes variations (casse, espaces)
            found = False
            for header in headers:
                if header.lower().strip() == column_name.lower().strip():
                    found = True
                    break
            if not found:
                missing_fields.append(column_name)
        
        if missing_fields:
            from import_export import exceptions
            raise exceptions.FieldError(
                f"The following fields are declared in 'import_id_fields' but are not present in the file headers: {', '.join(missing_fields)}"
            )
    
    def before_import_row(self, row, **kwargs):
        """
        Valide et prépare les données avant l'import.
        S'assure que le champ 'nom de compte' est présent et non vide.
        """
        # Vérifier que le compte est fourni
        compte_value = row.get('nom de compte', '').strip()
        if not compte_value:
            raise ValueError(
                "Le champ 'nom de compte' est obligatoire pour créer une famille. "
                "Veuillez fournir un nom de compte valide."
            )
    
    def get_or_init_instance(self, instance_loader, row):
        """
        Surcharge pour utiliser le column_name 'nom de famille' 
        au lieu du nom de champ 'name' lors de la recherche.
        Gère aussi les variations de casse et d'espaces.
        """
        # Mapper le column_name vers le nom de champ (gérer les variations)
        for key in row.keys():
            if key.lower().strip() == 'nom de famille':
                row['name'] = row[key]
                break
        return super().get_or_init_instance(instance_loader, row)

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
        widget=AutoCreateRegroupementWidget(RegroupementEmplacement, 'nom')
    )

    location_reference = fields.Field(
        column_name='location reference',
        attribute='location_reference'
    )

    class Meta:
        model = Location
        fields = ('location_reference', 'location_type', 'sous_zone', 'regroupement')
        import_id_fields = ('location_reference',)



from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Product, Family  # adapte selon tes modèles
from django.db import transaction


from import_export import resources, fields, exceptions
from import_export.widgets import ForeignKeyWidget, BooleanWidget
from .models import Product, Family

class ProductResource(resources.ModelResource):
    short_description = fields.Field(column_name='short description', attribute='Short_Description')
    barcode = fields.Field(column_name='barcode', attribute='Barcode')
    product_group = fields.Field(column_name='product group', attribute='Product_Group')
    stock_unit = fields.Field(column_name='stock unit', attribute='Stock_Unit')
    product_status = fields.Field(column_name='product status', attribute='Product_Status')
    internal_product_code = fields.Field(column_name='internal product code', attribute='Internal_Product_Code')
    product_family = fields.Field(
        column_name='product family',
        attribute='Product_Family',
        widget=ForeignKeyWidget(Family, 'family_name')
    )
    n_lot = fields.Field(column_name='n lot', attribute='n_lot', widget=BooleanWidget())
    n_serie = fields.Field(column_name='n serie', attribute='n_serie', widget=BooleanWidget())
    dlc = fields.Field(column_name='dlc', attribute='dlc', widget=BooleanWidget())

    class Meta:
        model = Product
        fields = (
            'short_description', 'barcode', 'product_group', 'stock_unit',
            'product_status', 'internal_product_code', 'product_family',
            'n_lot', 'n_serie', 'dlc'
        )
        import_id_fields = ('barcode',)
        skip_unchanged = True
        report_skipped = True
        use_transactions = True
        batch_size = 500  # Import par lots pour éviter timeout

    # Vérifie que toutes les lignes ont un product_family existant

    def before_import_row(self, row, **kwargs):
        family_name = row.get('product family')
        if not family_name or not family_name.strip():
            raise exceptions.ImportError(
                "La colonne 'product family' est obligatoire pour chaque produit."
            )
        if not Family.objects.filter(family_name=family_name.strip()).exists():
            raise exceptions.ImportError(
                f"La famille '{family_name}' n'existe pas dans la base de données."
            )


    # Surcharge pour gérer les variations de noms de colonne pour barcode
    def get_or_init_instance(self, instance_loader, row):
        field_variations = {
            'barcode': ['barcode', 'Barcode', 'BARCODE', 'code-barres', 'code barres', 'Code-Barres'],
        }
        for field_name, variations in field_variations.items():
            for key in row.keys():
                if key.lower().strip() in [v.lower().strip() for v in variations]:
                    row[field_name] = row[key]
                    break
        return super().get_or_init_instance(instance_loader, row)

    # Vérifie les import_id_fields
    def _check_import_id_fields(self, headers):
        field_to_columns = {
            'barcode': ['barcode', 'Barcode', 'BARCODE', 'code-barres', 'code barres', 'Code-Barres'],
        }
        normalized_headers = {h.lower().strip(): h for h in headers}
        available_headers = ', '.join(headers[:10])
        if len(headers) > 10:
            available_headers += f', ... ({len(headers)} en-têtes au total)'
        missing_fields = []
        for field_name in self.get_import_id_fields():
            possible_columns = field_to_columns.get(field_name, [field_name])
            found = False
            for possible_column in possible_columns:
                if possible_column.lower().strip() in normalized_headers:
                    found = True
                    break
            if not found:
                missing_fields.append(field_name)
        if missing_fields:
            raise exceptions.FieldError(
                f"The following fields are declared in 'import_id_fields' but are not present in the file headers: {', '.join(missing_fields)}. "
                f"En-têtes disponibles dans le fichier: {available_headers}"
            )



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


class PersonneResource(resources.ModelResource):
    """
    Resource pour l'import/export des personnes
    """
    nom = fields.Field(column_name='nom', attribute='nom')
    prenom = fields.Field(column_name='prénom', attribute='prenom')

    class Meta:
        model = Personne
        fields = ('nom', 'prenom')
        import_id_fields = ('nom', 'prenom')


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
    
    class Media:
        js = ('admin/js/import_async_button.js',)
    
    def changelist_view(self, request, extra_context=None):
        from django.urls import reverse
        extra_context = extra_context or {}
        extra_context['show_async_import'] = True
        extra_context['import_async_url'] = reverse('admin:masterdata_product_import_async')
        return super().changelist_view(request, extra_context)

    def get_family_name(self, obj):
        return obj.Product_Family.family_name if obj.Product_Family else '-'
    get_family_name.short_description = 'Famille'
    get_family_name.admin_order_field = 'Product_Family__family_name'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Si c'est un nouveau produit
            form.base_fields['reference'] = forms.CharField(required=False, widget=forms.HiddenInput())
        return form
    
    def get_urls(self):
        urls = super().get_urls()
        from django.urls import path
        custom_urls = [
            path(
                'import-async/',
                self.admin_site.admin_view(self.import_async_view),
                name='masterdata_product_import_async',
            ),
            path(
                'import-status/<int:task_id>/',
                self.admin_site.admin_view(self.import_status_view),
                name='masterdata_product_import_status',
            ),
            path(
                'import-errors/<int:task_id>/',
                self.admin_site.admin_view(self.import_errors_view),
                name='masterdata_product_import_errors',
            ),
            path(
                'import-errors-file/<int:task_id>/',
                self.admin_site.admin_view(self.download_errors_file),
                name='masterdata_product_download_errors',
            ),
        ]
        return custom_urls + urls
    
    def import_async_view(self, request):
        """Vue pour démarrer un import asynchrone (mode tout ou rien)"""
        from django.contrib import messages
        from django.shortcuts import redirect
        from django.template.response import TemplateResponse
        from django.utils.html import format_html
        from django.urls import reverse
        import tempfile
        import time
        import threading
        import os
        from .models import ImportTask
        from .services.import_service import ProductImportService
        
        if request.method == 'POST':
            if 'import_file' not in request.FILES:
                messages.error(request, "Aucun fichier fourni")
                return redirect('admin:masterdata_product_changelist')
            
            uploaded_file = request.FILES['import_file']
            
            # Sauvegarder le fichier temporairement
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(
                temp_dir, 
                f'import_product_{request.user.id}_{int(time.time())}.xlsx'
            )
            
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Créer la tâche d'import
            import_task = ImportTask.objects.create(
                user=request.user,
                file_path=file_path,
                file_name=uploaded_file.name,
                status='PENDING',
            )
            
            # Démarrer le traitement en arrière-plan
            service = ProductImportService(ProductResource)
            thread = threading.Thread(
                target=service.process_file_chunked,
                args=(file_path, import_task),
                daemon=True
            )
            thread.start()
            
            messages.success(
                request,
                format_html(
                    'Import démarré en mode "tout ou rien" en arrière-plan. '
                    '<a href="{}">Suivre la progression</a>',
                    reverse('admin:masterdata_product_import_status', args=[import_task.id])
                )
            )
            
            return redirect('admin:masterdata_product_changelist')
        
        # GET: Afficher le formulaire
        context = {
            **self.admin_site.each_context(request),
            'title': 'Import asynchrone de produits (tout ou rien)',
            'opts': self.model._meta,
        }
        return TemplateResponse(
            request,
            'admin/masterdata/product/import_async.html',
            context
        )
    
    def import_status_view(self, request, task_id):
        """Vue pour suivre le statut d'un import"""
        from django.http import JsonResponse
        from django.template.response import TemplateResponse
        from django.shortcuts import get_object_or_404
        from .models import ImportTask
        
        import_task = get_object_or_404(ImportTask, id=task_id, user=request.user)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Requête AJAX pour mise à jour
            progress = 0
            if import_task.total_rows > 0:
                if import_task.status == 'VALIDATING':
                    progress = int((import_task.validated_rows / import_task.total_rows) * 50)  # 50% max pour validation
                elif import_task.status == 'PROCESSING':
                    progress = 50 + int((import_task.processed_rows / import_task.total_rows) * 50)  # 50-100% pour import
                elif import_task.status in ['COMPLETED', 'CANCELLED', 'FAILED']:
                    progress = 100
            
            return JsonResponse({
                'status': import_task.status,
                'progress': progress,
                'validated_rows': import_task.validated_rows,
                'processed_rows': import_task.processed_rows,
                'total_rows': import_task.total_rows,
                'imported_count': import_task.imported_count,
                'updated_count': import_task.updated_count,
                'error_count': import_task.error_count,
                'error_message': import_task.error_message,
                'has_errors_file': bool(import_task.errors_file_path),
            })
        
        # Vue HTML
        context = {
            **self.admin_site.each_context(request),
            'import_task': import_task,
            'opts': self.model._meta,
        }
        return TemplateResponse(
            request,
            'admin/masterdata/product/import_status.html',
            context
        )
    
    def import_errors_view(self, request, task_id):
        """Vue pour afficher les erreurs détaillées"""
        from django.template.response import TemplateResponse
        from django.shortcuts import get_object_or_404
        from .models import ImportTask, ImportError
        
        import_task = get_object_or_404(ImportTask, id=task_id, user=request.user)
        errors = ImportError.objects.filter(import_task=import_task).order_by('row_number')
        
        context = {
            **self.admin_site.each_context(request),
            'import_task': import_task,
            'errors': errors,
            'opts': self.model._meta,
        }
        return TemplateResponse(
            request,
            'admin/masterdata/product/import_errors.html',
            context
        )
    
    def download_errors_file(self, request, task_id):
        """Télécharger le fichier Excel des erreurs"""
        from django.contrib import messages
        from django.shortcuts import redirect, get_object_or_404
        from django.http import FileResponse
        from .models import ImportTask
        
        import_task = get_object_or_404(ImportTask, id=task_id, user=request.user)
        
        if not import_task.errors_file_path or not os.path.exists(import_task.errors_file_path):
            messages.error(request, "Le fichier d'erreurs n'existe pas.")
            return redirect('admin:masterdata_product_import_status', task_id=task_id)
        
        return FileResponse(
            open(import_task.errors_file_path, 'rb'),
            as_attachment=True,
            filename=f'erreurs_import_{import_task.id}.xlsx'
        )


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
    exclude = ('created_at', 'updated_at', 'deleted_at', 'is_deleted')
    readonly_fields = ('reference',)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj and 'reference' in form.base_fields:  # Si c'est une nouvelle personne
            # Permettre au champ reference d'être vide lors de la création
            form.base_fields['reference'].required = False
            form.base_fields['reference'].widget = forms.HiddenInput()
        return form
    
    def save_model(self, request, obj, form, change):
        # S'assurer que la référence est générée si elle est vide
        if not obj.reference:
            obj.reference = obj.generate_reference(obj.REFERENCE_PREFIX)
        super().save_model(request, obj, form, change)


@admin.register(ImportTask)
class ImportTaskAdmin(admin.ModelAdmin):
    """Admin pour les tâches d'import"""
    list_display = ('id', 'file_name', 'user', 'status', 'total_rows', 'imported_count', 'error_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('file_name', 'user__username', 'user__email')
    readonly_fields = ('file_path', 'file_name', 'user', 'total_rows', 'validated_rows', 'processed_rows', 
                      'imported_count', 'updated_count', 'error_count', 'status', 'error_message', 
                      'errors_file_path', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('file_name', 'user', 'status', 'created_at', 'updated_at')
        }),
        ('Progression', {
            'fields': ('total_rows', 'validated_rows', 'processed_rows')
        }),
        ('Résultats', {
            'fields': ('imported_count', 'updated_count', 'error_count')
        }),
        ('Erreurs', {
            'fields': ('error_message', 'errors_file_path'),
            'classes': ('collapse',)
        }),
        ('Fichier', {
            'fields': ('file_path',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Les tâches sont créées automatiquement
    
    def has_change_permission(self, request, obj=None):
        return False  # Les tâches ne peuvent pas être modifiées manuellement


@admin.register(ImportError)
class ImportErrorAdmin(admin.ModelAdmin):
    """Admin pour les erreurs d'import"""
    list_display = ('row_number', 'import_task', 'error_type', 'field_name', 'error_message', 'created_at')
    list_filter = ('error_type', 'import_task', 'created_at')
    search_fields = ('error_message', 'field_name', 'import_task__file_name')
    readonly_fields = ('import_task', 'row_number', 'error_type', 'error_message', 'field_name', 
                      'field_value', 'row_data', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations', {
            'fields': ('import_task', 'row_number', 'error_type', 'created_at', 'updated_at')
        }),
        ('Détails de l\'erreur', {
            'fields': ('error_message', 'field_name', 'field_value')
        }),
        ('Données de la ligne', {
            'fields': ('row_data',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Les erreurs sont créées automatiquement
    
    def has_change_permission(self, request, obj=None):
        return False  # Les erreurs ne peuvent pas être modifiées manuellement












