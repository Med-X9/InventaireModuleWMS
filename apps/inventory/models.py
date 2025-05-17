from django.db import models
from simple_history.models import HistoricalRecords
from apps.masterdata.models import Account,TimeStampedModel,Warehouse,Location,Product
from apps.users.models import UserWeb
import hashlib
from django.utils import timezone
import random
import string
import uuid

# Create your models here.

class ReferenceMixin:
    """
    Mixin pour la génération automatique de référence
    """
    def generate_reference(self, prefix):
        """
        Génère une référence unique
        Format: {PREFIX}{encrypted_id}{encrypted_created_at}
        """
        # Générer un identifiant unique temporaire
        temp_id = str(uuid.uuid4())[:8]
        
        # Créer une chaîne à crypter
        data_to_hash = f"{temp_id}{timezone.now().timestamp()}"
        
        # Générer un hash MD5 et prendre les 8 premiers caractères
        hash_value = hashlib.md5(data_to_hash.encode()).hexdigest()[:8].upper()
        
        # Créer la référence
        reference = f"{prefix}{hash_value}"
        
        return reference

    def save(self, *args, **kwargs):
        # S'assurer que la référence est générée avant la sauvegarde
        if not hasattr(self, 'reference') or not self.reference:
            self.reference = self.generate_reference(self.REFERENCE_PREFIX)
        super().save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Générer la référence dès l'initialisation
        if not hasattr(self, 'reference') or not self.reference:
            self.reference = self.generate_reference(self.REFERENCE_PREFIX)

class Inventory(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'INV'
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CURRENT', 'Current'),
        ('LAUNCH', 'LAUNCH'),  
        ('END', 'End'),
    )

    reference = models.CharField(max_length=50, unique=True, null=False)
    label = models.CharField(max_length=200)  
    date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)  
    pending_status_date = models.DateTimeField(null=True, blank=True)
    current_status_date = models.DateTimeField(null=True, blank=True)
    lunch_status_date = models.DateTimeField(null=True, blank=True)
    end_status_date = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.label


class Setting(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'SET'
    reference = models.CharField(unique=True, max_length=20, null=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='awi_links')
    warehouse = models.ForeignKey('masterdata.Warehouse', on_delete=models.CASCADE, related_name='awi_links')
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='awi_links')
    history = HistoricalRecords()    

    def __str__(self):
        return f"{self.account} - {self.warehouse} - {self.inventory}"


class Planning(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'PLN'
    
    reference = models.CharField(unique=True, max_length=20, null=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True,null=True)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    history = HistoricalRecords()    
    def __str__(self):
        return f"{self.warehouse} - {self.inventory}"
    
    
class Counting(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'CNT'
    
    STATUS_CHOICES = (
        ('LAUNCH', 'Launch'), 
        ('END', 'End'),
    )

    reference = models.CharField(max_length=20, unique=True, null=False)
    order = models.IntegerField()
    count_mode = models.CharField(max_length=100) 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)  
    date_status_lunch = models.DateTimeField(null=True, blank=True) 
    date_status_end = models.DateTimeField(null=True, blank=True)    
    unit_scanned = models.BooleanField(default=False)
    entry_quantity = models.BooleanField(default=False)
    is_variant = models.BooleanField(default=False) 
    stock_situation = models.BooleanField(default=False)
    quantity_show = models.BooleanField(default=False)
    inventory = models.ForeignKey('Inventory', on_delete=models.CASCADE, related_name='countings')
    history = HistoricalRecords()

    def __str__(self):
        return self.reference


class Job(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'JOB'
    
    STATUS_CHOICES = (
        ('LAUNCH', 'Launch'),  
        ('START', 'Start'),
        ('END', 'End'),
    )
    
    reference = models.CharField(max_length=20, unique=True, null=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)  
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    lunch_date = models.DateTimeField(null=True, blank=True)
    is_lunch = models.BooleanField(default=False)
    warehouse = models.ForeignKey('masterdata.Warehouse', on_delete=models.CASCADE)
    counting = models.ForeignKey('Counting', on_delete=models.CASCADE,blank=True,null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.reference
    



class Pda(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'PDA'
    
    reference = models.CharField(unique=True, max_length=20, null=False)
    lebel = models.CharField(max_length=200)
    session = models.ForeignKey(UserWeb, on_delete=models.CASCADE)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='pdas')
    history = HistoricalRecords()
    
    def __str__(self):
        return self.lebel
    
    
class Personne(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'PER'
    reference = models.CharField(unique=True, max_length=20, null=False)
    nom = models.CharField(max_length=200)
    prenom = models.CharField(max_length=200)
    history = HistoricalRecords()    
    def __str__(self):
        return f"{self.nom} - {self.prenom}"
    
    

class JobDetail(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'JBD' 
    reference = models.CharField(unique=True, max_length=20, null=False)
    pda = models.ForeignKey('Pda', on_delete=models.CASCADE, null=True, blank=True)
    location = models.ForeignKey('masterdata.Location', on_delete=models.CASCADE)
    job = models.ForeignKey('Job', on_delete=models.CASCADE)
    personne = models.ForeignKey('Personne', on_delete=models.CASCADE, related_name='primary_job_details',null=True,blank=True)
    personne_two = models.ForeignKey('Personne', on_delete=models.CASCADE, related_name='secondary_job_details',null=True,blank=True)
    is_lunch = models.BooleanField(default=False)
    status = models.CharField(max_length=50)  
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.job.reference} - {self.pda} - {self.location}"
    
    

class InventoryDetail(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'INVD'
    reference = models.CharField(unique=True, max_length=20, null=False)
    quantity_inventoried = models.IntegerField()
    product = models.ForeignKey('masterdata.Product',on_delete=models.CASCADE,blank=True,null=True)
    location = models.ForeignKey('masterdata.Location',on_delete=models.CASCADE)
    counting = models.ForeignKey(Counting,on_delete=models.CASCADE)
    history = HistoricalRecords()
    
    
    
class EcartComptage(TimeStampedModel, ReferenceMixin): 
    REFERENCE_PREFIX = 'ECT'
    reference = models.CharField(unique=True, max_length=20, null=False)
    ligne_comptage_1 = models.ForeignKey(InventoryDetail, on_delete=models.CASCADE, related_name='ecart_ligne_1')
    ligne_comptage_2 = models.ForeignKey(InventoryDetail, on_delete=models.CASCADE, related_name='ecart_ligne_2')
    ligne_comptage_3 = models.ForeignKey(InventoryDetail, on_delete=models.CASCADE, related_name='ecart_ligne_3')
    ecart_1_2 = models.IntegerField()
    result = models.IntegerField()
    justification = models.TextField(blank=True, null=True)  # Peut être vide au début
    resolved = models.BooleanField(default=False)
    history = HistoricalRecords()

    def __str__(self):
        return f"Ecart entre {self.ligne_comptage_1} et {self.ligne_comptage_2} (Résolu: {self.resolved})"
 

    


