"""
Repository pour l'affectation automatique des jobs depuis InventoryLocationJob
"""
from typing import List, Dict, Optional, Tuple
from django.db.models import QuerySet
from ..models import Job, Counting, Assigment, Inventory
from apps.users.models import UserApp
from apps.masterdata.models import InventoryLocationJob


class AutoAssignmentRepository:
    """
    Repository pour gérer l'accès aux données liées à l'affectation automatique
    """
    
    def get_inventory_by_id(self, inventory_id: int) -> Optional[Inventory]:
        """
        Récupère un inventaire par son ID
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            Instance d'Inventory ou None si non trouvé
        """
        try:
            return Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            return None
    
    def get_location_jobs_by_inventory(self, inventory_id: int) -> QuerySet:
        """
        Récupère tous les InventoryLocationJob pour un inventaire donné
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            QuerySet d'InventoryLocationJob
        """
        return InventoryLocationJob.objects.filter(
            inventaire_id=inventory_id,
            is_deleted=False
        ).select_related('inventaire', 'emplacement')
    
    def get_teams_by_usernames(self, usernames: List[str]) -> QuerySet:
        """
        Récupère les équipes (UserApp) par leurs usernames
        
        Args:
            usernames: Liste des usernames à chercher
            
        Returns:
            QuerySet de UserApp
        """
        return UserApp.objects.filter(
            username__in=usernames,
            type='Mobile',
            is_active=True
        )
    
    def get_counting_by_inventory_and_order(
        self, 
        inventory_id: int, 
        order: int
    ) -> Optional[Counting]:
        """
        Récupère un comptage par inventaire et ordre
        
        Args:
            inventory_id: ID de l'inventaire
            order: Ordre du comptage (1 ou 2)
            
        Returns:
            Instance de Counting ou None si non trouvé
        """
        return Counting.objects.filter(
            inventory_id=inventory_id, 
            order=order
        ).first()
    
    def get_active_general_inventories_excluding(
        self, 
        excluded_id: int
    ) -> QuerySet:
        """
        Récupère tous les inventaires GENERAL actifs en excluant un ID
        
        Args:
            excluded_id: ID de l'inventaire à exclure
            
        Returns:
            QuerySet d'Inventory
        """
        return Inventory.objects.filter(
            inventory_type='GENERAL',
            status__in=['EN PREPARATION', 'EN REALISATION']
        ).exclude(id=excluded_id)
    
    def get_conflicting_assignments(
        self, 
        usernames: List[str], 
        inventories: QuerySet
    ) -> QuerySet:
        """
        Récupère les assignments en conflit pour des équipes et inventaires donnés
        
        Args:
            usernames: Liste des usernames des équipes
            inventories: QuerySet des inventaires à vérifier
            
        Returns:
            QuerySet d'Assigment
        """
        return Assigment.objects.filter(
            session__username__in=usernames,
            job__inventory__in=inventories
        ).select_related('session', 'job__inventory')
    
    def get_jobs_by_references_and_inventory(
        self, 
        references: List[str], 
        inventory_id: int
    ) -> QuerySet:
        """
        Récupère les jobs par leurs références et l'ID de l'inventaire
        
        Args:
            references: Liste des références de jobs
            inventory_id: ID de l'inventaire
            
        Returns:
            QuerySet de Job
        """
        return Job.objects.filter(
            reference__in=references,
            inventory_id=inventory_id
        )
    
    def get_or_create_assignment(
        self,
        job: Job,
        counting: Counting,
        session: UserApp,
        reference: str,
        status: str,
        affecte_date,
        date_start
    ) -> Tuple[Assigment, bool]:
        """
        Crée ou récupère un assignment
        
        Args:
            job: Instance de Job
            counting: Instance de Counting
            session: Instance de UserApp (équipe)
            reference: Référence de l'assignment
            status: Statut de l'assignment
            affecte_date: Date d'affectation
            date_start: Date de début
            
        Returns:
            Tuple (Assigment, created: bool)
        """
        return Assigment.objects.get_or_create(
            job=job,
            counting=counting,
            defaults={
                'reference': reference,
                'session': session,
                'status': status,
                'affecte_date': affecte_date,
                'date_start': date_start
            }
        )
    
    def update_assignment(
        self,
        assignment: Assigment,
        session: UserApp,
        status: str,
        affecte_date,
        date_start,
        transfert_date=None
    ) -> Assigment:
        """
        Met à jour un assignment existant
        
        Args:
            assignment: Instance d'Assigment à mettre à jour
            session: Nouvelle équipe
            status: Nouveau statut
            affecte_date: Nouvelle date d'affectation
            date_start: Nouvelle date de début
            transfert_date: Date de transfert (optionnel)
            
        Returns:
            Instance d'Assigment mise à jour
        """
        assignment.session = session
        assignment.status = status
        assignment.affecte_date = affecte_date
        assignment.date_start = date_start
        
        if transfert_date:
            assignment.transfert_date = transfert_date
        
        assignment.save()
        return assignment
    
    def update_job_status(
        self,
        job: Job,
        status: str,
        affecte_date
    ) -> Job:
        """
        Met à jour le statut d'un job
        
        Args:
            job: Instance de Job à mettre à jour
            status: Nouveau statut
            affecte_date: Date d'affectation
            
        Returns:
            Instance de Job mise à jour
        """
        job.status = status
        job.affecte_date = affecte_date
        job.save()
        return job

    def get_assignments_by_job_and_countings(
        self,
        job: Job,
        countings: List[Counting]
    ) -> QuerySet:
        """
        Récupère les assignments pour un job et une liste de comptages

        Args:
            job: Instance de Job
            countings: Liste d'instances de Counting

        Returns:
            QuerySet d'Assigment
        """
        counting_ids = [counting.id for counting in countings if counting]
        return Assigment.objects.filter(
            job=job,
            counting_id__in=counting_ids
        )

