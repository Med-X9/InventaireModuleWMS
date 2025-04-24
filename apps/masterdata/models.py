from django.db import models
from django.core.validators import MinValueValidator
from simple_history.models import HistoricalRecords

# Create your models here.

from django.utils import timezone


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
        abstract = True  # Important : rend la classe non créable comme table

    def soft_delete(self):
        """Effectue une suppression logique (soft delete)."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()




class Account(TimeStampedModel):
    statuts = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
        ('OBSOLETE', 'OBSOLETE'),
    )
    
    account_code = models.CharField(unique=True,max_length=20)
    account_name = models.CharField(max_length=100)
    account_statuts = models.CharField(choices=statuts)
    description = models.TextField(null=True,blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.account_name


class Family(TimeStampedModel):
    STATUS_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
        ('OBSOLETE', 'OBSOLETE'),
    )
    
    family_code = models.CharField(max_length=20, unique=True)
    family_name = models.CharField(max_length=100)
    family_description = models.TextField(blank=True, null=True)
    compte = models.ForeignKey('Account', on_delete=models.CASCADE)  
    family_status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    history = HistoricalRecords()

    
    def __str__(self):
        return self.family_name
    
    

class Warehouse(TimeStampedModel):
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
    address = models.CharField(max_length=255,blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.warehouse_name
    
    

class ZoneType(TimeStampedModel):
    STATUS_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
    )
    
    type_code = models.CharField(unique=True,max_length=20)
    type_name = models.CharField(max_length=100)
    description = models.TextField(max_length=100,null=True,blank=True)
    status = models.CharField(choices=STATUS_CHOICES)
    history = HistoricalRecords()
    def __str__(self):
        return self.type_name
    

class Zone(TimeStampedModel):
    STATUS_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
        ('BLOCKED', 'BLOCKED'),
    )
    
    zone_code = models.CharField(unique=True,max_length=20)
    warehouse_id = models.ForeignKey(Warehouse,on_delete=models.CASCADE)
    zone_name = models.CharField(max_length=100)
    zone_type_id = models.ForeignKey(ZoneType,models.CASCADE)
    description = models.TextField(max_length=100,null=True,blank=True)
    zone_status = models.CharField(choices=STATUS_CHOICES)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.zone_name
    
    
class LocationType(TimeStampedModel):
    code = models.CharField(unique=True,max_length=20)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=100,blank=True,null=True)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()
    def __str__(self):
        return self.name
    

class Location(TimeStampedModel):
    location_code = models.CharField(unique=True,max_length=20)
    zone_id = models.ForeignKey(Zone,on_delete=models.CASCADE)
    location_type_id = models.ForeignKey(LocationType,on_delete=models.CASCADE)
    capacity = models.IntegerField(null=True,blank=True,validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    description = models.TextField(max_length=100,null=True,blank=True)
    history = HistoricalRecords()
    def __str__(self):
        return self.location_code
    
    

class Product(TimeStampedModel):
    
    
    STATUS_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
        ('OBSOLETE', 'OBSOLETE'),
    )
    
    
    reference = models.CharField(unique=True)
    Short_Description = models.CharField(max_length=100)
    Barcode = models.CharField(unique=True,max_length=30,null=True,blank=True)
    Product_Group = models.CharField(max_length=10)
    Stock_Unit = models.CharField(max_length=3)
    Product_Status = models.CharField(choices=STATUS_CHOICES)
    Internal_Product_Code = models.CharField(max_length=20)
    Product_Family = models.ForeignKey(Family,on_delete=models.CASCADE)
    parent_product = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    Is_Variant = models.BooleanField()
    history = HistoricalRecords()
    def __str__(self):
        return self.Short_Description
    
    

class UnitOfMeasure(TimeStampedModel):
    code = models.CharField(max_length=20,unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=100,null=True,blank=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name
    
    

class Stock(models.Model):
    location = models.ForeignKey(Location,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity_available = models.DecimalField(max_digits=12,decimal_places=3,validators=[MinValueValidator(0)])
    quantity_reserved = models.DecimalField(max_digits=12,decimal_places=3,validators=[MinValueValidator(0)],blank=True,null=True)
    quantity_in_transit = models.DecimalField(max_digits=12,decimal_places=3,validators=[MinValueValidator(0)],blank=True,null=True)
    quantity_in_receiving = models.DecimalField(max_digits=12,decimal_places=3,validators=[MinValueValidator(0)],blank=True,null=True)
    unit_of_measure = models.ForeignKey(UnitOfMeasure,on_delete=models.CASCADE)
    history = HistoricalRecords()