"""
Service pour l'affectation des ressources aux jobs.
"""
from typing import Dict, Any, List
from django.utils import timezone
from django.db import transaction
from ..interfaces.resource_assignment_interface import IResourceAssignmentService
from ..repositories.resource_assignment_repository import ResourceAssignmentRepository
from ..exceptions.resource_assignment_exceptions import (
    ResourceAssignmentValidationError, 
    ResourceAssignmentBusinessRuleError,
    ResourceAssignmentNotFoundError,
    ResourceAssignmentConflictError
)
from ..models import Job, JobDetailRessource
from apps.masterdata.models import Ressource

class ResourceAssignmentService(IResourceAssignmentService):
    """Service pour l'affectation des ressources aux jobs."""
    
    def __init__(self, repository: ResourceAssignmentRepository = None):
        self.repository = repository or ResourceAssignmentRepository()

    def assign_resources_to_job(self, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Affecte des ressources à un job
        
        Args:
            assignment_data: Données d'affectation contenant job_id, resource_ids, quantities
            
        Returns:
            Dict[str, Any]: Résultat de l'affectation
        """
        # Validation des données
        self.validate_resource_assignment_data(assignment_data)
        
        job_id = assignment_data['job_id']
        resource_assignments = assignment_data['resource_assignments']
        
        with transaction.atomic():
            # Vérifier que le job existe
            job = self.repository.get_job_by_id(job_id)
            if not job:
                raise ResourceAssignmentNotFoundError(f"Job avec l'ID {job_id} non trouvé")
            
            # Vérifier que le job n'est pas en statut EN ATTENTE
            if job.status == 'EN ATTENTE':
                raise ResourceAssignmentBusinessRuleError(
                    f"Les ressources ne peuvent pas être affectées aux jobs en statut 'EN ATTENTE'. "
                    f"Job {job.reference} doit d'abord être validé."
                )
            
            # Traiter chaque affectation de ressource
            assignments_created = 0
            assignments_updated = 0
            
            for resource_assignment in resource_assignments:
                resource_id = resource_assignment['resource_id']
                quantity = resource_assignment.get('quantity', 1)
                
                # Vérifier que la ressource existe
                resource = self.repository.get_resource_by_id(resource_id)
                if not resource:
                    raise ResourceAssignmentNotFoundError(f"Ressource avec l'ID {resource_id} non trouvée")
                
                # Vérifier s'il existe déjà une affectation pour cette ressource
                existing_assignment = self.repository.get_existing_job_resource(job_id, resource_id)
                
                if existing_assignment:
                    # Mettre à jour l'affectation existante
                    self.repository.update_job_resource(
                        existing_assignment,
                        quantity=quantity
                    )
                    assignments_updated += 1
                else:
                    # Créer une nouvelle affectation
                    assignment_data = {
                        'job': job,
                        'ressource': resource,
                        'quantity': quantity
                    }
                    
                    self.repository.create_job_resource(assignment_data)
                    assignments_created += 1
            
            total_assignments = assignments_created + assignments_updated
            
            return {
                'success': True,
                'message': f"{assignments_created} affectations créées, {assignments_updated} affectations mises à jour",
                'assignments_created': assignments_created,
                'assignments_updated': assignments_updated,
                'total_assignments': total_assignments,
                'job_id': job_id,
                'job_reference': job.reference
            }

    def assign_resources_to_jobs_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Affecte les mêmes ressources à plusieurs jobs
        
        Args:
            batch_data: Données d'affectation en lot contenant job_ids et resource_assignments
            
        Returns:
            Dict[str, Any]: Résultat de l'affectation en lot
        """
        # Validation des données
        self.validate_batch_resource_assignment_data(batch_data)
        
        job_ids = batch_data['job_ids']
        resource_assignments = batch_data['resource_assignments']
        
        # Validation préalable de tous les jobs avant de commencer les affectations
        jobs_to_process = []
        for job_id in job_ids:
            job = self.repository.get_job_by_id(job_id)
            if not job:
                raise ResourceAssignmentNotFoundError(f"Job avec l'ID {job_id} non trouvé")
            
            # Vérifier les règles métier
            if job.status == 'EN ATTENTE':
                raise ResourceAssignmentBusinessRuleError(f"Les ressources ne peuvent pas être affectées au job {job.reference} en statut 'EN ATTENTE'")
            
            jobs_to_process.append(job)
        
        # Validation préalable de toutes les ressources
        resources_to_assign = []
        for resource_assignment in resource_assignments:
            resource_id = resource_assignment['resource_id']
            resource = self.repository.get_resource_by_id(resource_id)
            if not resource:
                raise ResourceAssignmentNotFoundError(f"Ressource avec l'ID {resource_id} non trouvée")
            resources_to_assign.append(resource)
        
        # Si toutes les validations passent, procéder aux affectations dans une transaction
        with transaction.atomic():
            total_jobs_processed = 0
            total_assignments_created = 0
            total_assignments_updated = 0
            job_results = []
            
            for job in jobs_to_process:
                assignments_created = 0
                assignments_updated = 0
                
                for resource_assignment in resource_assignments:
                    resource_id = resource_assignment['resource_id']
                    quantity = resource_assignment.get('quantity', 1)
                    
                    # Récupérer la ressource (déjà validée)
                    resource = next(r for r in resources_to_assign if r.id == resource_id)
                    
                    # Vérifier s'il existe déjà une affectation pour cette ressource
                    existing_assignment = self.repository.get_existing_job_resource(job.id, resource_id)
                    
                    if existing_assignment:
                        # Mettre à jour l'affectation existante
                        self.repository.update_job_resource(
                            existing_assignment,
                            quantity=quantity
                        )
                        assignments_updated += 1
                    else:
                        # Créer une nouvelle affectation
                        assignment_data = {
                            'job': job,
                            'ressource': resource,
                            'quantity': quantity
                        }
                        
                        self.repository.create_job_resource(assignment_data)
                        assignments_created += 1
                
                total_assignments = assignments_created + assignments_updated
                
                job_results.append({
                    'success': True,
                    'message': f"{assignments_created} affectations créées, {assignments_updated} affectations mises à jour",
                    'assignments_created': assignments_created,
                    'assignments_updated': assignments_updated,
                    'total_assignments': total_assignments,
                    'job_id': job.id,
                    'job_reference': job.reference
                })
                
                total_jobs_processed += 1
                total_assignments_created += assignments_created
                total_assignments_updated += assignments_updated
            
            return {
                'success': True,
                'message': f"Traitement terminé pour {total_jobs_processed} jobs",
                'total_jobs_processed': total_jobs_processed,
                'total_assignments_created': total_assignments_created,
                'total_assignments_updated': total_assignments_updated,
                'job_results': job_results
            }

    def validate_batch_resource_assignment_data(self, batch_data: Dict[str, Any]) -> None:
        """
        Valide les données d'affectation de ressources en lot
        
        Args:
            batch_data: Données d'affectation en lot à valider
            
        Raises:
            ResourceAssignmentValidationError: Si les données sont invalides
        """
        errors = []
        
        # Validation des champs obligatoires
        if not batch_data.get('job_ids'):
            errors.append("La liste des IDs de jobs est obligatoire")
        
        if not batch_data.get('resource_assignments'):
            errors.append("La liste des affectations de ressources est obligatoire")
        
        # Validation des types
        job_ids = batch_data.get('job_ids', [])
        if not isinstance(job_ids, list) or not job_ids:
            errors.append("job_ids doit être une liste non vide")
        
        resource_assignments = batch_data.get('resource_assignments', [])
        if not isinstance(resource_assignments, list) or not resource_assignments:
            errors.append("resource_assignments doit être une liste non vide")
        
        # Validation de chaque job_id
        for i, job_id in enumerate(job_ids):
            if not isinstance(job_id, int):
                errors.append(f"job_id doit être un entier pour le job {i+1}")
        
        # Validation de chaque affectation de ressource
        for i, resource_assignment in enumerate(resource_assignments):
            if not isinstance(resource_assignment, dict):
                errors.append(f"L'affectation de ressource {i+1} doit être un objet")
                continue
            
            if not resource_assignment.get('resource_id'):
                errors.append(f"resource_id est obligatoire pour l'affectation de ressource {i+1}")
            
            resource_id = resource_assignment.get('resource_id')
            if resource_id and not isinstance(resource_id, int):
                errors.append(f"resource_id doit être un entier pour l'affectation de ressource {i+1}")
            
            quantity = resource_assignment.get('quantity', 1)
            if quantity and not isinstance(quantity, int):
                errors.append(f"quantity doit être un entier pour l'affectation de ressource {i+1}")
            
            if quantity and quantity <= 0:
                errors.append(f"quantity doit être positif pour l'affectation de ressource {i+1}")
        
        if errors:
            raise ResourceAssignmentValidationError(" | ".join(errors))

    def validate_resource_assignment_data(self, assignment_data: Dict[str, Any]) -> None:
        """
        Valide les données d'affectation des ressources
        
        Args:
            assignment_data: Données d'affectation à valider
            
        Raises:
            ResourceAssignmentValidationError: Si les données sont invalides
        """
        errors = []
        
        # Validation des champs obligatoires
        if not assignment_data.get('job_id'):
            errors.append("L'ID du job est obligatoire")
        
        if not assignment_data.get('resource_assignments'):
            errors.append("La liste des affectations de ressources est obligatoire")
        
        # Validation des types
        job_id = assignment_data.get('job_id')
        if job_id and not isinstance(job_id, int):
            errors.append("job_id doit être un entier")
        
        resource_assignments = assignment_data.get('resource_assignments', [])
        if not isinstance(resource_assignments, list) or not resource_assignments:
            errors.append("resource_assignments doit être une liste non vide")
        
        # Validation de chaque affectation de ressource
        for i, resource_assignment in enumerate(resource_assignments):
            if not isinstance(resource_assignment, dict):
                errors.append(f"L'affectation de ressource {i+1} doit être un objet")
                continue
            
            if not resource_assignment.get('resource_id'):
                errors.append(f"resource_id est obligatoire pour l'affectation de ressource {i+1}")
            
            resource_id = resource_assignment.get('resource_id')
            if resource_id and not isinstance(resource_id, int):
                errors.append(f"resource_id doit être un entier pour l'affectation de ressource {i+1}")
            
            quantity = resource_assignment.get('quantity', 1)
            if quantity and not isinstance(quantity, int):
                errors.append(f"quantity doit être un entier pour l'affectation de ressource {i+1}")
            
            if quantity and quantity <= 0:
                errors.append(f"quantity doit être positif pour l'affectation de ressource {i+1}")
        
        if errors:
            raise ResourceAssignmentValidationError(" | ".join(errors))

    def get_job_resources(self, job_id: int) -> List[Any]:
        """
        Récupère les ressources affectées à un job
        
        Args:
            job_id: ID du job
            
        Returns:
            List[Any]: Liste des objets JobDetailRessource
        """
        try:
            # Vérifier que le job existe
            job = self.repository.get_job_by_id(job_id)
            if not job:
                raise ResourceAssignmentNotFoundError(f"Job avec l'ID {job_id} non trouvé")
            
            # Récupérer les ressources affectées
            job_resources = self.repository.get_job_resources(job_id)
            
            # Retourner directement les objets JobDetailRessource
            # Le serializer JobResourceDetailSerializer s'occupera de la sérialisation
            return job_resources
            
        except ResourceAssignmentNotFoundError:
            raise
        except Exception as e:
            raise ResourceAssignmentValidationError(f"Erreur lors de la récupération des ressources : {str(e)}")

    def remove_resources_from_job(self, job_id: int, resource_ids: List[int]) -> Dict[str, Any]:
        """
        Supprime des ressources d'un job
        
        Args:
            job_id: ID du job
            resource_ids: Liste des IDs des ressources à supprimer
            
        Returns:
            Dict[str, Any]: Résultat de la suppression
        """
        try:
            # Vérifier que le job existe
            job = self.repository.get_job_by_id(job_id)
            if not job:
                raise ResourceAssignmentNotFoundError(f"Job avec l'ID {job_id} non trouvé")
            
            # Vérifier que le job n'est pas en statut EN ATTENTE
            if job.status == 'EN ATTENTE':
                raise ResourceAssignmentBusinessRuleError(
                    f"Les ressources ne peuvent pas être supprimées des jobs en statut 'EN ATTENTE'. "
                    f"Job {job.reference} doit d'abord être validé."
                )
            
            # Supprimer les affectations
            deleted_count = self.repository.delete_job_resources(job_id, resource_ids)
            
            return {
                'success': True,
                'message': f"{deleted_count} affectations de ressources supprimées",
                'deleted_count': deleted_count,
                'job_id': job_id,
                'job_reference': job.reference
            }
            
        except (ResourceAssignmentNotFoundError, ResourceAssignmentBusinessRuleError):
            raise
        except Exception as e:
            raise ResourceAssignmentValidationError(f"Erreur lors de la suppression des ressources : {str(e)}") 