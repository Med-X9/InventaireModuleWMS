from typing import List, Dict, Any, Optional
from django.db import transaction
from django.db.models import Q
from ..interfaces.job_interface import JobRepositoryInterface
from ..models import Job, Assigment, Counting, Inventory, JobDetail
from apps.masterdata.models import Warehouse, Location
from django.utils import timezone

class JobRepository(JobRepositoryInterface):
    """
    Repository pour l'accès aux données des jobs
    Contient uniquement les opérations CRUD
    """
    
    def create_job(self, **kwargs) -> Job:
        """Crée un job"""
        return Job.objects.create(**kwargs)
    
    def create_job_detail(self, **kwargs) -> JobDetail:
        """Crée un job detail"""
        return JobDetail.objects.create(**kwargs)
    
    def create_assignment(self, **kwargs) -> Assigment:
        """Crée un assignment"""
        return Assigment.objects.create(**kwargs)
    
    def get_inventory_by_id(self, inventory_id: int) -> Optional[Inventory]:
        """Récupère un inventaire par ID"""
        try:
            return Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            return None
    
    def get_warehouse_by_id(self, warehouse_id: int) -> Optional[Warehouse]:
        """Récupère un warehouse par ID"""
        try:
            return Warehouse.objects.get(id=warehouse_id)
        except Warehouse.DoesNotExist:
            return None
    
    def get_location_by_id(self, location_id: int) -> Optional[Location]:
        """Récupère un emplacement par ID"""
        try:
            return Location.objects.get(id=location_id)
        except Location.DoesNotExist:
            return None
    
    def get_countings_by_inventory(self, inventory: Inventory) -> List[Counting]:
        """Récupère les comptages d'un inventaire"""
        return list(Counting.objects.filter(inventory=inventory).order_by('order'))
    
    def get_job_by_id(self, job_id: int) -> Optional[Job]:
        """Récupère un job par ID"""
        try:
            return Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return None
    
    def get_jobs_by_warehouse(self, warehouse_id: int) -> List[Job]:
        """Récupère tous les jobs d'un warehouse"""
        return list(Job.objects.filter(warehouse_id=warehouse_id).order_by('-created_at'))
    
    def get_jobs_by_inventory(self, inventory_id: int) -> List[Job]:
        """Récupère tous les jobs d'un inventaire"""
        return list(Job.objects.filter(inventory_id=inventory_id).order_by('-created_at'))
    
    def get_pending_jobs_by_warehouse(self, warehouse_id: int) -> List[Dict[str, Any]]:
        """Récupère les jobs en attente d'un warehouse"""
        return list(Job.objects.filter(
            warehouse_id=warehouse_id,
            status='EN ATTENTE'
        ).values('id', 'reference').order_by('created_at'))
    
    def get_pending_jobs_by_warehouse_with_filters(self, warehouse_id: int, filters: Optional[Dict[str, Any]] = None) -> List[Job]:
        """Récupère les jobs en attente d'un warehouse avec filtres et relations préchargées"""
        queryset = Job.objects.filter(
            warehouse_id=warehouse_id,
            status='EN ATTENTE'
        ).select_related(
            'inventory',
            'warehouse'
        ).prefetch_related(
            'jobdetail_set',
            'assigment_set'
        )
        
        # Appliquer les filtres django-filter si fournis
        if filters:
            from ..filters.job_filters import PendingJobFilter
            filter_instance = PendingJobFilter(filters, queryset=queryset)
            queryset = filter_instance.qs
        
        return list(queryset.order_by('-created_at'))
    
    def get_job_details_by_job(self, job: Job) -> List[JobDetail]:
        """Récupère les job details d'un job"""
        return list(JobDetail.objects.filter(job=job))
    
    def get_job_details_by_job_and_locations(self, job: Job, location_ids: List[int]) -> List[JobDetail]:
        """Récupère les job details d'un job pour des emplacements spécifiques"""
        return list(JobDetail.objects.filter(job=job, location_id__in=location_ids))
    
    def get_job_detail_by_job_and_location(self, job: Job, location: Location) -> Optional[JobDetail]:
        """Récupère un job detail pour un job et un emplacement spécifiques"""
        return JobDetail.objects.filter(job=job, location=location).first()
    
    def get_job_detail_by_job_location_and_counting(self, job: Job, location: Location, counting: Counting) -> Optional[JobDetail]:
        """Récupère un job detail pour un job, un emplacement et un comptage spécifiques"""
        return JobDetail.objects.filter(job=job, location=location, counting=counting).first()
    
    def get_existing_job_detail_by_location_and_inventory(self, location: Location, inventory: Inventory) -> Optional[JobDetail]:
        """Récupère un job detail existant pour un emplacement et un inventaire"""
        return JobDetail.objects.filter(
            location=location,
            job__inventory=inventory
        ).first()
    
    def get_existing_job_detail_by_location_and_job(self, location: Location, job: Job) -> Optional[JobDetail]:
        """Récupère un job detail existant pour un emplacement et un job"""
        return JobDetail.objects.filter(job=job, location=location).first()
    
    def get_existing_job_detail_by_location_and_inventory_exclude_job(self, location: Location, inventory: Inventory, job: Job) -> Optional[JobDetail]:
        """Récupère un job detail existant pour un emplacement et un inventaire, en excluant un job"""
        return JobDetail.objects.filter(
            location=location,
            job__inventory=inventory
        ).exclude(job=job).first()
    
    def get_jobs_by_ids(self, job_ids: List[int]) -> List[Job]:
        """Récupère des jobs par leurs IDs"""
        return list(Job.objects.filter(id__in=job_ids))
    
    def get_assignments_by_job(self, job: Job) -> List[Assigment]:
        """Récupère les assignments d'un job"""
        return list(Assigment.objects.filter(job=job))
    
    def delete_job_details(self, job_details: List[JobDetail]) -> int:
        """Supprime des job details et retourne le nombre supprimé"""
        if not job_details:
            return 0
        # Supprimer tous les job details en une seule opération
        job_detail_ids = [jd.id for jd in job_details]
        deleted_count, _ = JobDetail.objects.filter(id__in=job_detail_ids).delete()
        return deleted_count
    
    def delete_job_detail(self, job_detail: JobDetail) -> None:
        """Supprime un job detail spécifique"""
        job_detail.delete()
    
    def delete_assignments_by_job(self, job: Job) -> int:
        """Supprime tous les assignments d'un job"""
        return Assigment.objects.filter(job=job).delete()[0]
    
    def delete_job_details_by_job(self, job: Job) -> int:
        """Supprime tous les job details d'un job"""
        return JobDetail.objects.filter(job=job).delete()[0]
    
    def delete_job(self, job: Job) -> None:
        """Supprime un job"""
        job.delete()
    
    def update_job_status(self, job: Job, status: str, **kwargs) -> None:
        """Met à jour le statut d'un job"""
        job.status = status
        for key, value in kwargs.items():
            setattr(job, key, value)
        job.save()
    
    def get_jobs_with_filters(self, warehouse_id: int, filters: Optional[Dict[str, Any]] = None) -> List[Job]:
        """Récupère des jobs avec filtres"""
        queryset = Job.objects.filter(warehouse_id=warehouse_id)
        
        if filters:
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            if 'inventory' in filters:
                queryset = queryset.filter(inventory_id=filters['inventory'])
            if 'reference' in filters:
                queryset = queryset.filter(reference__icontains=filters['reference'])
            if 'created_at_gte' in filters:
                queryset = queryset.filter(created_at__gte=filters['created_at_gte'])
            if 'created_at_lte' in filters:
                queryset = queryset.filter(created_at__lte=filters['created_at_lte'])
        
        return list(queryset.order_by('-created_at'))
    
    def get_jobs_for_datatable(self):
        """
        Récupère tous les jobs avec leurs relations préchargées pour optimiser les requêtes.
        Utilisé par les vues DataTable.
        """
        return Job.objects.select_related(
            'warehouse',
            'inventory'
        ).prefetch_related(
            'jobdetail_set__location__sous_zone__zone',
            'jobdetail_set__location__sous_zone',
            'assigment_set__counting',
            'assigment_set__session',
            'jobdetailressource_set__ressource'
        )
    
    def get_jobs_for_inventory_warehouse_datatable(self, inventory_id: int, warehouse_id: int):
        """
        Récupère les jobs d'un inventaire et warehouse spécifiques avec relations préchargées.
        Utilisé par les vues DataTable.
        """
        return Job.objects.filter(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id
        ).select_related(
            'warehouse',
            'inventory'
        ).prefetch_related(
            'jobdetail_set__location__sous_zone__zone',
            'jobdetail_set__location__sous_zone',
            'assigment_set__counting',
            'assigment_set__session',
            'jobdetailressource_set__ressource'
        )
    
    def get_pending_jobs_for_warehouse_datatable(self, warehouse_id: int):
        """
        Récupère les jobs en attente pour un warehouse avec relations préchargées.
        Utilisé par les vues DataTable.
        """
        return Job.objects.filter(
            warehouse_id=warehouse_id,
            status='EN ATTENTE'
        ).select_related(
            'inventory',
            'warehouse'
        ).prefetch_related(
            'jobdetail_set',
            'assigment_set'
        )
    
    def get_validated_jobs_datatable(self, warehouse_id: Optional[int] = None, inventory_id: Optional[int] = None):
        """
        Récupère les jobs validés, affectés, transférés ou prêts avec relations préchargées.
        Utilisé par les vues DataTable.
        
        Statuts inclus : VALIDE, AFFECTE, TRANSFERT, PRET
        """
        queryset = Job.objects.filter(status__in=['VALIDE', 'AFFECTE', 'TRANSFERT', 'PRET'])
        
        if warehouse_id is not None:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        if inventory_id is not None:
            queryset = queryset.filter(inventory_id=inventory_id)
        
        return queryset.select_related(
            'warehouse', 'inventory'
        ).prefetch_related(
            'jobdetail_set__location__sous_zone__zone',
            'jobdetail_set__location__sous_zone',
            'assigment_set__counting',
            'assigment_set__session',
            'jobdetailressource_set__ressource'
        )
    
    def get_pending_jobs_datatable(self):
        """
        Récupère tous les jobs en attente avec relations préchargées.
        Utilisé par les vues DataTable.
        """
        return Job.objects.filter(status='EN ATTENTE').select_related(
            'warehouse',
            'inventory'
        ).prefetch_related(
            'jobdetail_set__location__sous_zone__zone',
            'jobdetail_set__location__sous_zone',
            'assigment_set__counting',
            'assigment_set__session',
            'jobdetailressource_set__ressource'
        ) 