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
    
    def get_existing_assignment_for_job(self, job_id: int) -> Optional[Any]:
        """
        Récupère l'affectation existante pour un job spécifique
        Si plusieurs affectations existent pour le même job, supprime les doublons et retourne la plus récente
        Une session peut être affectée à plusieurs jobs différents
        
        Args:
            job_id: ID du job
            
        Returns:
            Optional[Any]: L'affectation existante ou None
        """
        assignments = Assigment.objects.filter(job_id=job_id).order_by('-created_at')
        
        if not assignments.exists():
            return None
        
        # Si une seule affectation pour ce job, la retourner
        if assignments.count() == 1:
            return assignments.first()
        
        # Si plusieurs affectations pour le même job, garder la plus récente et supprimer les autres
        latest_assignment = assignments.first()
        
        # Supprimer les affectations plus anciennes pour ce job
        assignments.exclude(id=latest_assignment.id).delete()
        
        return latest_assignment
    
    def get_existing_assignment_for_job_and_counting(self, job_id: int, counting_id: int) -> Optional[Any]:
        """
        Récupère l'affectation existante pour un job et un comptage spécifiques
        
        Args:
            job_id: ID du job
            counting_id: ID du comptage
            
        Returns:
            Optional[Any]: L'affectation existante ou None
        """
        try:
            return Assigment.objects.get(job_id=job_id, counting_id=counting_id)
        except Assigment.DoesNotExist:
            return None
    
    def get_assignment_by_job_and_order(self, job_id: int, counting_order: int) -> Optional[Any]:
        """
        Récupère l'affectation pour un job et un ordre de comptage.
        """
        return Assigment.objects.filter(
            job_id=job_id,
            counting__order=counting_order
        ).order_by('-created_at').first()
    
    def get_assignments_by_session(self, session_id: int) -> List[Any]:
        """
        Récupère toutes les affectations d'une session
        
        Args:
            session_id: ID de la session
            
        Returns:
            List[Any]: Liste des affectations de la session
        """
        return Assigment.objects.filter(session_id=session_id).order_by('-created_at')
    
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
    
    def get_assignments_by_session_with_jobs(self, session_id: int) -> List[Any]:
        """
        Récupère toutes les affectations d'une session avec leurs jobs associés
        
        Args:
            session_id: ID de la session (équipe)
            
        Returns:
            List[Any]: Liste des affectations avec leurs jobs (optimisée avec select_related)
        """
        return Assigment.objects.filter(
            session_id=session_id
        ).select_related(
            'job',
            'job__inventory',
            'job__warehouse',
            'counting',
            'session'
        ).order_by('-created_at') 