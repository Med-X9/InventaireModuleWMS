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
        Format: {PREFIX}-{id}-{timestamp}-{hash}
        """
        # Si l'objet n'a pas encore d'ID (création), utiliser un UUID temporaire
        if not self.id:
            temp_id = str(uuid.uuid4())[:6]  # Réduire à 6 caractères
            timestamp = int(timezone.now().timestamp())
            # Utiliser seulement les 4 derniers chiffres du timestamp
            timestamp_short = str(timestamp)[-4:]
            data_to_hash = f"{temp_id}{timestamp}"
            hash_value = hashlib.md5(data_to_hash.encode()).hexdigest()[:4].upper()  # Réduire à 4 caractères
            reference = f"{prefix}-{temp_id}-{timestamp_short}-{hash_value}"
        else:
            # Si l'objet a un ID, utiliser la méthode normale
            timestamp = int(self.created_at.timestamp())
            # Utiliser seulement les 4 derniers chiffres du timestamp
            timestamp_short = str(timestamp)[-4:]
            data_to_hash = f"{self.id}{timestamp}"
            hash_value = hashlib.md5(data_to_hash.encode()).hexdigest()[:4].upper()  # Réduire à 4 caractères
            reference = f"{prefix}-{self.id}-{timestamp_short}-{hash_value}"
        
        # S'assurer que la référence ne dépasse pas 20 caractères
        if len(reference) > 20:
            # Tronquer la référence si nécessaire
            reference = reference[:20]
        
        return reference

    def save(self, *args, **kwargs):
        # Générer la référence si elle n'existe pas
        if not self.reference:
            self.reference = self.generate_reference(self.REFERENCE_PREFIX)
        super().save(*args, **kwargs)


class Inventory(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'INV'
    
    STATUS_CHOICES = (
        ('EN PREPARATION', 'EN PREPARATION'),
        ('EN REALISATION', 'EN REALISATION'),
        ('TERMINE', 'TERMINE'),  
        ('CLOTURE', 'CLOTURE'),
        
    )
    
    INVENTORY_TYPE_CHOICES = (
        ('TOURNANT', 'TOURNANT'),
        ('GENERAL', 'GENERAL'),
    )

    reference = models.CharField(max_length=50, unique=True, null=False)
    label = models.CharField(max_length=200)  
    date = models.DateTimeField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    inventory_type = models.CharField(max_length=20, choices=INVENTORY_TYPE_CHOICES, default='GENERAL')
    en_preparation_status_date = models.DateTimeField(null=True, blank=True)
    en_realisation_status_date = models.DateTimeField(null=True, blank=True)
    termine_status_date = models.DateTimeField(null=True, blank=True)
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
        ('AFFECTE', 'AFFECTE'),
        ('PRET', 'PRET'),
        ('TRANSFERT', 'TRANSFERT'), 
        ('ENTAME', 'ENTAME'),
        ('VALIDE', 'VALIDE'),
        ('TERMINE', 'TERMINE'),
    )
   
    
    reference = models.CharField(max_length=20, unique=True, null=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    en_attente_date = models.DateTimeField(null=True, blank=True)
    affecte_date = models.DateTimeField(null=True, blank=True)
    pret_date = models.DateTimeField(null=True, blank=True)
    transfert_date = models.DateTimeField(null=True, blank=True)
    entame_date = models.DateTimeField(null=True, blank=True)
    valide_date = models.DateTimeField(null=True, blank=True)
    termine_date = models.DateTimeField(null=True, blank=True)
    warehouse = models.ForeignKey('masterdata.Warehouse', on_delete=models.CASCADE)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
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
    counting = models.ForeignKey('Counting', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=50)  
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.job.reference} - {self.location}"
    


class Assigment(TimeStampedModel, ReferenceMixin):

    STATUS_CHOICES = (
        ('EN ATTENTE', 'EN ATTENTE'),
        ('AFFECTE', 'AFFECTE'),
        ('PRET', 'PRET'),
        ('TRANSFERT', 'TRANSFERT'), 
        ('ENTAME', 'ENTAME'),
        ('TERMINE', 'TERMINE'),
    )
    REFERENCE_PREFIX = 'ASS'
    reference = models.CharField(unique=True, max_length=20, null=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    transfert_date = models.DateTimeField(null=True, blank=True)
    entame_date = models.DateTimeField(null=True, blank=True)
    affecte_date = models.DateTimeField(null=True, blank=True)
    pret_date = models.DateTimeField(null=True, blank=True)
    job = models.ForeignKey('Job', on_delete=models.CASCADE)
    date_start = models.DateTimeField(null=True, blank=True)
    session = models.ForeignKey('users.UserApp', on_delete=models.CASCADE, null=True, blank=True, limit_choices_to={'type': 'Mobile'})
    personne = models.ForeignKey('Personne', on_delete=models.CASCADE, related_name='primary_job_details',null=True,blank=True)
    personne_two = models.ForeignKey('Personne', on_delete=models.CASCADE, related_name='secondary_job_details',null=True,blank=True)   
    counting = models.ForeignKey(Counting, on_delete=models.CASCADE)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Affectation')
        verbose_name_plural = _('Affectations')
    
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
        return f"{self.inventory.reference} - {self.ressource} - {self.quantity}"


class CountingDetail(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'CD'
    reference = models.CharField(unique=True, max_length=20, null=False)
    quantity_inventoried = models.IntegerField()
    product = models.ForeignKey('masterdata.Product',on_delete=models.CASCADE,blank=True,null=True)
    dlc = models.DateField(null=True,blank=True)
    n_lot = models.CharField(max_length=100,null=True,blank=True)
    location = models.ForeignKey('masterdata.Location',on_delete=models.CASCADE)
    counting = models.ForeignKey(Counting,on_delete=models.CASCADE)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()
    

class NSerieInventory(TimeStampedModel, ReferenceMixin):
    REFERENCE_PREFIX = 'NS'
    reference = models.CharField(unique=True, max_length=20, null=False)
    n_serie = models.CharField(max_length=100,null=True,blank=True)
    counting_detail = models.ForeignKey(CountingDetail,on_delete=models.CASCADE)
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.counting_detail.product.Short_Description} - {self.n_serie}"



    
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
 

    


