from django.db import models
from django.core.validators import MinValueValidator
from simple_history.models import HistoricalRecords
import hashlib
from django.utils import timezone
from apps.masterdata.mixins import CodeGeneratorMixin
from django.apps import apps

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
    
    account_code = models.CharField(unique=True, max_length=20)
    account_name = models.CharField(max_length=100)
    account_statuts = models.CharField(choices=(
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
        ('OBSOLETE', 'OBSOLETE'),
    ))
    description = models.TextField(null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.account_name

class Family(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les familles de produits
    """
    CODE_PREFIX = 'FAM'
    
    family_code = models.CharField(max_length=20, unique=True)
    family_name = models.CharField(max_length=100)
    family_description = models.TextField(blank=True, null=True)
    compte = models.ForeignKey('Account', on_delete=models.CASCADE)  
    family_status = models.CharField(max_length=10, choices=(
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
        ('OBSOLETE', 'OBSOLETE'),
    ))
    history = HistoricalRecords()

    def __str__(self):
        return self.family_name

class Warehouse(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les entrepôts
    """
    CODE_PREFIX = 'WH'
    
    STATUS_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
    )
    
    Warehouse_CHOICES = (
        ('CENTRAL', 'CENTRAL'),
        ('RECEIVING', 'RECEIVING'),
        ('SHIPPING', 'SHIPPING'),
        ('TRANSIT', 'TRANSIT'),
    )
    
    warehouse_code = models.CharField(max_length=20, unique=True)
    warehouse_name = models.CharField(max_length=100)
    warehouse_type = models.CharField(choices=Warehouse_CHOICES)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES)
    address = models.CharField(max_length=255, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.warehouse_name

class ZoneType(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les types de zones
    """
    CODE_PREFIX = 'ZT'
    
    STATUS_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
    )
    
    type_code = models.CharField(unique=True, max_length=20)
    type_name = models.CharField(max_length=100)
    description = models.TextField(max_length=100, null=True, blank=True)
    status = models.CharField(choices=STATUS_CHOICES)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.type_name

class Zone(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les zones
    """
    CODE_PREFIX = 'Z'
    
    STATUS_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
        ('BLOCKED', 'BLOCKED'),
    )
    
    zone_code = models.CharField(unique=True, max_length=20)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    zone_name = models.CharField(max_length=100)
    zone_type = models.ForeignKey(ZoneType, models.CASCADE)
    description = models.TextField(max_length=100, null=True, blank=True)
    zone_status = models.CharField(choices=STATUS_CHOICES)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.zone_name

class SousZone(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les sous zones
    """
    CODE_PREFIX = 'SZ'
    
    STATUS_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
        ('BLOCKED', 'BLOCKED'),
    )
    
    sous_zone_code = models.CharField(unique=True, max_length=20)
    sous_zone_name = models.CharField(max_length=100)
    zone = models.ForeignKey(Zone, models.CASCADE)
    description = models.TextField(max_length=100, null=True, blank=True)
    sous_zone_status = models.CharField(choices=STATUS_CHOICES)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.sous_zone_name

class LocationType(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les types d'emplacements
    """
    CODE_PREFIX = 'LT'
    
    code = models.CharField(unique=True, max_length=20)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name

class Location(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les emplacements
    """
    CODE_PREFIX = 'LOC'
    
    location_code = models.CharField(unique=True, max_length=20)
    location_reference = models.CharField(unique=True, max_length=30)
    sous_zone = models.ForeignKey(SousZone, on_delete=models.CASCADE)
    location_type = models.ForeignKey(LocationType, on_delete=models.CASCADE)
    capacity = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    description = models.TextField(max_length=100, null=True, blank=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.location_reference

class Product(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les produits
    """
    CODE_PREFIX = 'PRD'
    
    STATUS_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
        ('OBSOLETE', 'OBSOLETE'),
    )
    
    reference = models.CharField(unique=True)
    Short_Description = models.CharField(max_length=100)
    Barcode = models.CharField(unique=True, max_length=30, null=True, blank=True)
    Product_Group = models.CharField(max_length=10)
    Stock_Unit = models.CharField(max_length=3)
    Product_Status = models.CharField(choices=STATUS_CHOICES)
    Internal_Product_Code = models.CharField(max_length=20)
    Product_Family = models.ForeignKey(Family, on_delete=models.CASCADE)
    parent_product = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    Is_Variant = models.BooleanField()
    history = HistoricalRecords()
    
    def __str__(self):
        return self.Short_Description

class UnitOfMeasure(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les unités de mesure
    """
    CODE_PREFIX = 'UOM'
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=100, null=True, blank=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name

class Stock(TimeStampedModel):
    """
    Modèle pour les stocks
    """
    reference = models.CharField(unique=True, max_length=20)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_available = models.DecimalField(max_digits=12, decimal_places=3, validators=[MinValueValidator(0)])
    quantity_reserved = models.DecimalField(max_digits=12, decimal_places=3, validators=[MinValueValidator(0)], blank=True, null=True)
    quantity_in_transit = models.DecimalField(max_digits=12, decimal_places=3, validators=[MinValueValidator(0)], blank=True, null=True)
    quantity_in_receiving = models.DecimalField(max_digits=12, decimal_places=3, validators=[MinValueValidator(0)], blank=True, null=True)
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
    


class Ressource(CodeGeneratorMixin, TimeStampedModel):
    STATUS_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
    )
    CODE_PREFIX = 'RES'
    reference = models.CharField(unique=True, max_length=20)
    libelle = models.CharField(max_length=100)
    description = models.TextField(max_length=100, null=True, blank=True)
    status = models.CharField(choices=STATUS_CHOICES)
    history = HistoricalRecords()

    def __str__(self):
        return self.libelle


class Procedure(CodeGeneratorMixin, TimeStampedModel):
    """
    Modèle pour les procédures
    """
