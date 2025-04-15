from django.db import models

# Create your models here.



class Account(models.Model):
    statuts = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
        ('OBSOLETE', 'OBSOLETE'),
    )
    
    account_code = models.CharField(unique=True,max_length=20)
    account_name = models.CharField(max_length=100)
    account_statuts = models.CharField(choices=statuts)
    description = models.models.TextField()
    
    def __str__(self):
        return self.account_name


class Family(models.Model):
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

    def __str__(self):
        return self.family_name
    
    

class Warehouse(models.Model):
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
    
    def __str__(self):
        return self.warehouse_name
    
    

class ZoneType(models.Model):
    type_code = models.CharField(unique=True,max_length=20)
    type_name = models.CharField(max_length=20)
    description = models.TextField(max_length=100,null=True,blank=True)
    