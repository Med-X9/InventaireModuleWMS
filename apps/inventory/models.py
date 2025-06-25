from django.db import models
from simple_history.models import HistoricalRecords
from apps.masterdata.models import Account,TimeStampedModel,Warehouse,Location,Product
from apps.users.models import UserApp
import hashlib
from django.utils import timezone
import random
import string
import uuid
from django.utils.translation import gettext_lazy as _

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
        ('EN PREPARATION', 'EN PREPARATION'),
        ('EN REALISATION', 'EN REALISATION'),
        ('TERMINE', 'TERMINE'),  
        ('CLOTURE', 'CLOTURE'),
    )

    reference = models.CharField(max_length=50, unique=True, null=False)
    label = models.CharField(max_length=200)  
    date = models.DateTimeField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)  
    en_preparation_status_date = models.DateTimeField(null=True, blank=True)
    en_realisation_status_date = models.DateTimeField(null=True, blank=True)
    ternime_status_date = models.DateTimeField(null=True, blank=True)
    cloture_status_date = models.DateTimeField(null=True, blank=True)

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
    
    reference = models.CharField(_('Référence'), unique=True, max_length=20, null=False)
    start_date = models.DateTimeField(_('Date de début'))
    end_date = models.DateTimeField(_('Date de fin'), blank=True, null=True)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, verbose_name=_('Inventaire'))
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name=_('Entrepôt'))
    history = HistoricalRecords()    

    class Meta:
        verbose_name = _('Planification')
        verbose_name_plural = _('Planifications')

    def __str__(self):
        return f"{self.warehouse} - {self.inventory}"
    
    
class Counting(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'CNT'
    
    

    reference = models.CharField(_('Référence'), max_length=20, unique=True, null=False)
    order = models.IntegerField(_('Ordre'))
    count_mode = models.CharField(_('Mode de comptage'), max_length=100)     
    unit_scanned = models.BooleanField(_('Unité scannée'), default=False)
    entry_quantity = models.BooleanField(_('Saisie de quantité'), default=False)
    is_variant = models.BooleanField(_('Est une variante'), default=False)
    n_lot = models.BooleanField(_('N° lot'), default=False)
    n_serie = models.BooleanField(_('N° série'), default=False)
    dlc = models.BooleanField(_('DLC'), default=False)
    show_product=models.BooleanField(_('Afficher le produit'), default=False)
    stock_situation = models.BooleanField(_('Situation de stock'), default=False)
    quantity_show = models.BooleanField(_('Afficher la quantité'), default=False)
    inventory = models.ForeignKey('Inventory', on_delete=models.CASCADE, related_name='countings', verbose_name=_('Inventaire'))
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Comptage')
        verbose_name_plural = _('Comptages')

    def __str__(self):
        return self.reference


class Job(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'JOB'
    
    STATUS_CHOICES = (
        ('EN ATTENTE', 'EN ATTENTE'),
        ('VALIDE', 'VALIDE'),
        ('AFFECTE', 'AFFECTE'),
        ('PRET', 'PRET'),
        ('TRANSFERT', 'TRANSFERT'), 
        ('ENTAME', 'ENTAME'),
        ('TERMINE', 'TERMINE'),
    )
   
    
    reference = models.CharField(max_length=20, unique=True, null=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    date_estime = models.DateTimeField(null=True, blank=True)
    transfert_date = models.DateTimeField(null=True, blank=True)
    en_attente_date = models.DateTimeField(null=True, blank=True)
    entame_date = models.DateTimeField(null=True, blank=True)
    valide_date = models.DateTimeField(null=True, blank=True)
    affecte_date = models.DateTimeField(null=True, blank=True)
    pret_date = models.DateTimeField(null=True, blank=True)
    termine_date = models.DateTimeField(null=True, blank=True)
    warehouse = models.ForeignKey('masterdata.Warehouse', on_delete=models.CASCADE)
    invetory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    history = HistoricalRecords()

    def __str__(self):
        return self.reference
    




    
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
    location = models.ForeignKey('masterdata.Location', on_delete=models.CASCADE)
    job = models.ForeignKey('Job', on_delete=models.CASCADE)   
    status = models.CharField(max_length=50)  
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.job.reference} - {self.location}"
    


class Assigment(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'ASS'
    reference = models.CharField(unique=True, max_length=20, null=False)
    job = models.ForeignKey('Job', on_delete=models.CASCADE)
    date_start = models.DateTimeField(null=True, blank=True)
    session = models.ForeignKey('users.UserApp', on_delete=models.CASCADE, null=True, blank=True,limit_choices_to={'role__name': 'Operateur'})
    personne = models.ForeignKey('Personne', on_delete=models.CASCADE, related_name='primary_job_details',null=True,blank=True)
    personne_two = models.ForeignKey('Personne', on_delete=models.CASCADE, related_name='secondary_job_details',null=True,blank=True)   
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.job.reference} - {self.personne} - {self.personne_two}"
    
class JobDetailRessource(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'JDR'
    reference = models.CharField(unique=True, max_length=20, null=False)
    job = models.ForeignKey('Job', on_delete=models.CASCADE)
    ressource = models.ForeignKey('masterdata.Ressource', on_delete=models.CASCADE)
    quantity = models.IntegerField(null=True, blank=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.job.reference} - {self.ressource} - {self.quantity}"
    


class InventoryDetailRessource(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'IDR'
    reference = models.CharField(unique=True, max_length=20, null=False)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    ressource = models.ForeignKey('masterdata.Ressource', on_delete=models.CASCADE)
    quantity = models.IntegerField(null=True, blank=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.job.reference} - {self.ressource} - {self.quantity}"


class CountingDetail(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'CD'
    reference = models.CharField(unique=True, max_length=20, null=False)
    quantity_inventoried = models.IntegerField()
    product = models.ForeignKey('masterdata.Product',on_delete=models.CASCADE,blank=True,null=True)
    location = models.ForeignKey('masterdata.Location',on_delete=models.CASCADE)
    counting = models.ForeignKey(Counting,on_delete=models.CASCADE)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()
    
    
    
class EcartComptage(TimeStampedModel, ReferenceMixin): 
    REFERENCE_PREFIX = 'ECT'
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    reference = models.CharField(unique=True, max_length=20, null=False)
    ligne_comptage_1 = models.ForeignKey(CountingDetail, on_delete=models.CASCADE, related_name='ecart_ligne_1',null=True,blank=True)
    ligne_comptage_2 = models.ForeignKey(CountingDetail, on_delete=models.CASCADE, related_name='ecart_ligne_2',null=True,blank=True)
    ligne_comptage_3 = models.ForeignKey(CountingDetail, on_delete=models.CASCADE, related_name='ecart_ligne_3',null=True,blank=True)
    ecart = models.IntegerField(null=True, blank=True)
    result = models.IntegerField(null=True, blank=True)
    justification = models.TextField(blank=True, null=True)  # Peut être vide au début
    resolved = models.BooleanField(default=False)
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(ecart__isnull=True) | models.Q(ecart__gte=0)
                ),
                name='ecart_positive_or_null'
            ),
            models.CheckConstraint(
                check=(
                    models.Q(result__isnull=True) | models.Q(result__gte=0)
                ),
                name='result_positive_or_null'
            )
        ]
    def __str__(self):
        return f"Ecart entre {self.ligne_comptage_1} et {self.ligne_comptage_2} (Résolu: {self.resolved})"
 

    


