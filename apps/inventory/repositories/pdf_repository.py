"""
Repository pour les opérations de données pour la génération PDF
"""
from typing import List, Optional
from ..interfaces.pdf_interface import PDFRepositoryInterface
from ..models import Inventory, Counting, Job, JobDetail, Assigment
from apps.masterdata.models import Stock


class PDFRepository(PDFRepositoryInterface):
    """Repository pour la génération PDF"""
    
    def get_inventory_by_id(self, inventory_id: int) -> Optional[Inventory]:
        """Récupère un inventaire par ID"""
        try:
            return Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            return None
    
    def get_counting_by_id(self, counting_id: int) -> Optional[Counting]:
        """Récupère un comptage par ID"""
        try:
            return Counting.objects.get(id=counting_id)
        except Counting.DoesNotExist:
            return None
    
    def get_countings_by_inventory(self, inventory: Inventory) -> List[Counting]:
        """Récupère tous les comptages d'un inventaire"""
        return list(Counting.objects.filter(inventory=inventory).order_by('order'))
    
    def get_all_jobs_by_inventory(self, inventory: Inventory) -> List[Job]:
        """Récupère tous les jobs d'un inventaire avec leurs détails"""
        return list(
            Job.objects.filter(
                inventory=inventory
            ).prefetch_related(
                'jobdetail_set__location',
                'assigment_set__counting',
                'assigment_set__session',
                'assigment_set__personne',
                'assigment_set__personne_two'
            )
        )
    
    def get_job_details_by_job(self, job: Job) -> List[JobDetail]:
        """Récupère les job details d'un job"""
        return list(
            job.jobdetail_set.select_related('location', 'counting').all()
        )
    
    def get_stocks_by_location_and_inventory(
        self, 
        location: 'Location', 
        inventory: Inventory
    ) -> List[Stock]:
        """Récupère les stocks d'un emplacement pour un inventaire"""
        return list(
            Stock.objects.filter(
                location=location,
                inventory=inventory
            ).select_related('product', 'unit_of_measure')
        )
    
    def get_jobs_by_counting(self, inventory: Inventory, counting: Counting) -> List[Job]:
        """Récupère les jobs d'un inventaire pour un comptage spécifique"""
        # Récupérer les job details qui ont ce comptage
        job_ids = JobDetail.objects.filter(
            job__inventory=inventory,
            counting=counting
        ).values_list('job_id', flat=True).distinct()
        
        return list(
            Job.objects.filter(
                id__in=job_ids
            ).prefetch_related(
                'jobdetail_set__location',
                'assigment_set__counting',
                'assigment_set__session',
                'assigment_set__personne',
                'assigment_set__personne_two'
            )
        )
    
    def get_assignments_by_job(self, job: Job) -> List[Assigment]:
        """Récupère les assignments d'un job"""
        return list(
            job.assigment_set.select_related(
                'counting',
                'session',
                'personne',
                'personne_two'
            ).all()
        )
