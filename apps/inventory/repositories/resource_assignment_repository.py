from typing import Dict, Any, List, Optional
from django.db import transaction
from ..interfaces.resource_assignment_interface import IResourceAssignmentRepository
from ..models import Job, JobDetailRessource
from apps.masterdata.models import Ressource

class ResourceAssignmentRepository(IResourceAssignmentRepository):
    """Repository pour l'affectation des ressources aux jobs"""
    
    def get_job_by_id(self, job_id: int) -> Optional[Job]:
        """Récupère un job par son ID"""
        try:
            return Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return None
    
    def get_resource_by_id(self, resource_id: int) -> Optional[Ressource]:
        """Récupère une ressource par son ID"""
        try:
            return Ressource.objects.get(id=resource_id)
        except Ressource.DoesNotExist:
            return None
    
    def get_existing_job_resource(self, job_id: int, resource_id: int) -> Optional[JobDetailRessource]:
        """Récupère une affectation ressource-job existante"""
        try:
            return JobDetailRessource.objects.get(job_id=job_id, ressource_id=resource_id)
        except JobDetailRessource.DoesNotExist:
            return None
    
    def create_job_resource(self, assignment_data: Dict[str, Any]) -> JobDetailRessource:
        """Crée une nouvelle affectation ressource-job"""
        job_resource = JobDetailRessource(**assignment_data)
        job_resource.save()
        return job_resource
    
    def update_job_resource(self, job_resource: JobDetailRessource, **kwargs) -> None:
        """Met à jour une affectation ressource-job"""
        for key, value in kwargs.items():
            setattr(job_resource, key, value)
        job_resource.save()
    
    def get_job_resources(self, job_id: int) -> List[JobDetailRessource]:
        """Récupère toutes les ressources affectées à un job"""
        return list(JobDetailRessource.objects.filter(job_id=job_id).select_related('ressource'))
    
    def delete_job_resources(self, job_id: int, resource_ids: List[int]) -> int:
        """Supprime des affectations ressource-job"""
        deleted_count, _ = JobDetailRessource.objects.filter(
            job_id=job_id,
            ressource_id__in=resource_ids
        ).delete()
        return deleted_count 