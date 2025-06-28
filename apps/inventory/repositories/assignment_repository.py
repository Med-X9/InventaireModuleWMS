from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import transaction
from ..interfaces.assignment_interface import IAssignmentRepository
from ..models import Job, Counting, Assigment
from ..exceptions.assignment_exceptions import AssignmentNotFoundError

class AssignmentRepository(IAssignmentRepository):
    """Repository pour l'affectation des jobs"""
    
    def get_jobs_by_ids(self, job_ids: List[int]) -> List[Any]:
        """
        Récupère les jobs par leurs IDs
        
        Args:
            job_ids: Liste des IDs des jobs
            
        Returns:
            List[Any]: Liste des jobs
        """
        jobs = Job.objects.filter(id__in=job_ids)
        if len(jobs) != len(job_ids):
            found_ids = set(jobs.values_list('id', flat=True))
            missing_ids = set(job_ids) - found_ids
            raise AssignmentNotFoundError(f"Jobs non trouvés: {missing_ids}")
        return list(jobs)
    
    def get_counting_by_order_and_inventory(self, order: int, inventory_id: int) -> Optional[Any]:
        """
        Récupère un comptage par ordre et inventaire
        
        Args:
            order: Ordre du comptage
            inventory_id: ID de l'inventaire
            
        Returns:
            Optional[Any]: Le comptage ou None
        """
        try:
            return Counting.objects.get(order=order, inventory_id=inventory_id)
        except Counting.DoesNotExist:
            return None
    
    def create_assignment(self, assignment_data: Dict[str, Any]) -> Any:
        """
        Crée une nouvelle affectation
        
        Args:
            assignment_data: Données de l'affectation
            
        Returns:
            Any: L'affectation créée
        """
        return Assigment.objects.create(**assignment_data)
    
    def update_job_status(self, job_id: int, status: str, date_field: str) -> None:
        """
        Met à jour le statut d'un job
        
        Args:
            job_id: ID du job
            status: Nouveau statut
            date_field: Champ de date à mettre à jour
        """
        update_data = {
            'status': status,
            date_field: timezone.now()
        }
        Job.objects.filter(id=job_id).update(**update_data)
    
    def get_existing_assignments_for_jobs(self, job_ids: List[int]) -> List[Any]:
        """
        Récupère les affectations existantes pour des jobs
        
        Args:
            job_ids: Liste des IDs des jobs
            
        Returns:
            List[Any]: Liste des affectations existantes
        """
        return Assigment.objects.filter(job_id__in=job_ids)
    
    def get_job_with_inventory(self, job_id: int) -> Optional[Any]:
        """
        Récupère un job avec son inventaire
        
        Args:
            job_id: ID du job
            
        Returns:
            Optional[Any]: Le job avec son inventaire ou None
        """
        try:
            return Job.objects.select_related('inventory').get(id=job_id)
        except Job.DoesNotExist:
            return None 