from django.db import models
from django.core.validators import MinValueValidator
from simple_history.models import HistoricalRecords
import hashlib
from django.utils import timezone
from apps.masterdata.mixins import CodeGeneratorMixin
from django.apps import apps
from django.utils.translation import gettext_lazy as _
import random
from datetime import datetime

class ReferenceMixin:
    """
    Mixin pour la génération automatique de référence
    """
    def generate_reference(self, prefix):
        """
        Génère une référence unique
        Format: {PREFIX}-{id}-{timestamp}-{hash}
        """
        timestamp = int(self.created_at.timestamp())
        data_to_hash = f"{self.id}{timestamp}"
        hash_value = hashlib.md5(data_to_hash.encode()).hexdigest()[:8].upper()
        return f"{prefix}-{self.id}-{timestamp}-{hash_value}"

    def save(self, *args, **kwargs):
        if not self.reference and self.id:
            self.reference = self.generate_reference(self.REFERENCE_PREFIX)
        super().save(*args, **kwargs)

# Create your models here.

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    objects = ActiveManager()
    class Meta:
        abstract = True

    def soft_delete(self):
        """Effectue une suppression logique (soft delete)."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

class Account(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les comptes
    """
    CODE_PREFIX = 'ACC'
    
    reference = models.CharField(_('Code du compte'), unique=True, max_length=20)
    account_name = models.CharField(_('Nom du compte'), max_length=100)
    account_statuts = models.CharField(_('Statut'), choices=(
        ('ACTIVE', _('Actif')),
        ('INACTIVE', _('Inactif')),
        ('OBSOLETE', _('Obsolète')),
    ))
    description = models.TextField(_('Description'), null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Compte')
        verbose_name_plural = _('Comptes')

    def __str__(self):
        return self.account_name

class Family(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les familles de produits
    """
    CODE_PREFIX = 'FAM'
    
    reference = models.CharField(_('Code de la famille'), max_length=20, unique=True)
    family_name = models.CharField(_('Nom de la famille'), max_length=100)
    family_description = models.TextField(_('Description'), blank=True, null=True)
    compte = models.ForeignKey('Account', on_delete=models.CASCADE, verbose_name=_('Compte'))
    family_status = models.CharField(_('Statut'), max_length=10, choices=(
        ('ACTIVE', _('Actif')),
        ('INACTIVE', _('Inactif')),
        ('OBSOLETE', _('Obsolète')),
    ))
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Famille')
        verbose_name_plural = _('Familles')

    def __str__(self):
        return self.family_name

class Warehouse(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les entrepôts
    """
    CODE_PREFIX = 'WH'
    
    STATUS_CHOICES = (
        ('ACTIVE', _('Actif')),
        ('INACTIVE', _('Inactif')),
    )
    
    Warehouse_CHOICES = (
        ('CENTRAL', _('Central')),
        ('RECEIVING', _('Réception')),
        ('SHIPPING', _('Expédition')),
        ('TRANSIT', _('Transit')),
    )
    
    reference = models.CharField(_('Code de l\'entrepôt'), max_length=20, unique=True)
    warehouse_name = models.CharField(_('Nom de l\'entrepôt'), max_length=100)
    warehouse_type = models.CharField(_('Type d\'entrepôt'), choices=Warehouse_CHOICES)
    description = models.TextField(_('Description'), blank=True, null=True)
    status = models.CharField(_('Statut'), choices=STATUS_CHOICES)
    address = models.CharField(_('Adresse'), max_length=255, blank=True, null=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Entrepôt')
        verbose_name_plural = _('Entrepôts')

    def __str__(self):
        return self.warehouse_name

class ZoneType(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les types de zones
    """
    CODE_PREFIX = 'ZT'
    
    STATUS_CHOICES = (
        ('ACTIVE', _('Actif')),
        ('INACTIVE', _('Inactif')),
    )
    
    reference = models.CharField(_('Code du type'), unique=True, max_length=20)
    type_name = models.CharField(_('Nom du type'), max_length=100)
    description = models.TextField(_('Description'), max_length=100, null=True, blank=True)
    status = models.CharField(_('Statut'), choices=STATUS_CHOICES)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Type de zone')
        verbose_name_plural = _('Types de zones')
    
    def __str__(self):
        return self.type_name

class Zone(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les zones
    """
    CODE_PREFIX = 'Z'
    
    STATUS_CHOICES = (
        ('ACTIVE', _('Actif')),
        ('INACTIVE', _('Inactif')),
        ('BLOCKED', _('Bloqué')),
    )
    
    reference = models.CharField(_('Code de la zone'), unique=True, max_length=20)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name=_('Entrepôt'))
    zone_name = models.CharField(_('Nom de la zone'), max_length=100)
    zone_type = models.ForeignKey(ZoneType, models.CASCADE, verbose_name=_('Type de zone'))
    description = models.TextField(_('Description'), max_length=100, null=True, blank=True)
    zone_status = models.CharField(_('Statut'), choices=STATUS_CHOICES)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Zone')
        verbose_name_plural = _('Zones')
    
    def __str__(self):
        return self.zone_name

class SousZone(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les sous zones
    """
    CODE_PREFIX = 'SZ'
    
    STATUS_CHOICES = (
        ('ACTIVE', _('Actif')),
        ('INACTIVE', _('Inactif')),
        ('BLOCKED', _('Bloqué')),
    )
    
    reference = models.CharField(_('Code de la sous-zone'), unique=True, max_length=20)
    sous_zone_name = models.CharField(_('Nom de la sous-zone'), max_length=100)
    zone = models.ForeignKey(Zone, models.CASCADE, verbose_name=_('Zone'))
    description = models.TextField(_('Description'), max_length=100, null=True, blank=True)
    sous_zone_status = models.CharField(_('Statut'), choices=STATUS_CHOICES)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Sous-zone')
        verbose_name_plural = _('Sous-zones')
    
    def __str__(self):
        return self.sous_zone_name

class LocationType(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les types d'emplacements
    """
    CODE_PREFIX = 'LT'
    
    reference = models.CharField(_('Code'), unique=True, max_length=20)
    name = models.CharField(_('Nom'), max_length=100)
    description = models.TextField(_('Description'), max_length=100, blank=True, null=True)
    is_active = models.BooleanField(_('Actif'), default=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Type d\'emplacement')
        verbose_name_plural = _('Types d\'emplacements')
    
    def __str__(self):
        return self.name

class Location(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les emplacements
    """
    CODE_PREFIX = 'LOC'
    
    reference = models.CharField(_('Code de l\'emplacement'), unique=True, max_length=20)
    location_reference = models.CharField(_('Référence de l\'emplacement'), unique=True, max_length=30)
    sous_zone = models.ForeignKey(SousZone, on_delete=models.CASCADE, verbose_name=_('Sous-zone'))
    location_type = models.ForeignKey(LocationType, on_delete=models.CASCADE, verbose_name=_('Type d\'emplacement'))
    capacity = models.IntegerField(_('Capacité'), null=True, blank=True, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(_('Actif'), default=True)
    description = models.TextField(_('Description'), max_length=100, null=True, blank=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Emplacement')
        verbose_name_plural = _('Emplacements')
    
    def __str__(self):
        return self.location_reference

class Product(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les produits
    """
    CODE_PREFIX = 'PRD'
    
    STATUS_CHOICES = (
        ('ACTIVE', _('Actif')),
        ('INACTIVE', _('Inactif')),
        ('OBSOLETE', _('Obsolète')),
    )
    
    reference = models.CharField(_('Référence'), unique=True, max_length=20)
    Internal_Product_Code = models.CharField(_('Code produit'), max_length=20,unique=True)
    Short_Description = models.CharField(_('Désignation'), max_length=100)
    Barcode = models.CharField(_('Code-barres'), unique=True, max_length=30, null=True, blank=True)
    Product_Group = models.CharField(_('Groupe de produit'), max_length=10,null=True, blank=True)
    Stock_Unit = models.CharField(_('Unité de stock'), max_length=3)
    Product_Status = models.CharField(_('Statut'), choices=STATUS_CHOICES)  
    Product_Family = models.ForeignKey(Family, on_delete=models.CASCADE, verbose_name=_('Famille de produit'))
    Is_Variant = models.BooleanField(_('variante'),default=False)
    n_lot=models.BooleanField(_('N° lot'),default=False)
    n_serie=models.BooleanField(_('N° série'),default=False)
    dlc = models.BooleanField(_('DLC'),default=False)
    parent_product = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('Produit parent'))
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Produit')
        verbose_name_plural = _('Produits')
    
    def __str__(self):
        return self.Short_Description

class UnitOfMeasure(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les unités de mesure
    """
    CODE_PREFIX = 'UOM'
    
    reference = models.CharField(_('Code'), max_length=20, unique=True)
    name = models.CharField(_('Nom'), max_length=50)
    description = models.TextField(_('Description'), max_length=100, null=True, blank=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Unité de mesure')
        verbose_name_plural = _('Unités de mesure')
    
    def __str__(self):
        return self.name

class Stock(TimeStampedModel):
    """
    Modèle pour les stocks
    """
    reference = models.CharField(unique=True, max_length=20)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,blank=True,null=True)
    quantity_available = models.IntegerField(validators=[MinValueValidator(0)])
    quantity_reserved = models.IntegerField(validators=[MinValueValidator(0)], blank=True, null=True)
    quantity_in_transit = models.IntegerField(validators=[MinValueValidator(0)], blank=True, null=True)
    quantity_in_receiving = models.IntegerField(validators=[MinValueValidator(0)], blank=True, null=True)
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE)
    inventory = models.ForeignKey('inventory.Inventory', on_delete=models.CASCADE)
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.reference:
            # Générer une référence unique basée sur l'ID et le timestamp
            timestamp = int(self.created_at.timestamp())
            data_to_hash = f"STK{self.id}{timestamp}"
            hash_value = hashlib.sha256(data_to_hash.encode()).hexdigest()[:8].upper()
            self.reference = f"STK-{timestamp}-{self.id}-{hash_value}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.Short_Description} - {self.location.location_code}"
    
class TypeRessource(CodeGeneratorMixin, TimeStampedModel):
    CODE_PREFIX = 'TR'
    reference = models.CharField(unique=True, max_length=20)
    libelle = models.CharField(max_length=100)
    description = models.TextField(max_length=100, null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.libelle

class Ressource(CodeGeneratorMixin, TimeStampedModel):
    STATUS_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
    )
    CODE_PREFIX = 'RES'
    reference = models.CharField(unique=True, max_length=20)
    libelle = models.CharField(max_length=100)
    description = models.TextField(max_length=100, null=True, blank=True)
    type_ressource = models.ForeignKey(TypeRessource, on_delete=models.CASCADE, verbose_name=_('Type de ressource'))
    status = models.CharField(choices=STATUS_CHOICES)
    history = HistoricalRecords()

    def __str__(self):
        return self.libelle


class Procedure(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les procédures
    """
