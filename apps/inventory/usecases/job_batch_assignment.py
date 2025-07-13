"""
Use case pour l'affectation en lot de sessions et ressources aux jobs
"""
from typing import List, Dict, Any
from django.db import transaction
from django.utils import timezone
from ..models import Job, Assigment, Counting
from ..exceptions import JobCreationError
from ..services.assignment_service import AssignmentService
from ..services.resource_assignment_service import ResourceAssignmentService
import logging

logger = logging.getLogger(__name__)

class JobBatchAssignmentUseCase:
    """
    Use case pour l'affectation en lot de sessions et ressources aux jobs
    """
    
    def __init__(self):
        self.assignment_service = AssignmentService()
        self.resource_assignment_service = ResourceAssignmentService()
    
    def execute(self, assignments_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Affecte des sessions et des ressources à plusieurs jobs en lot (nouveau format)
        S'arrête dès la première erreur
        """
        try:
            with transaction.atomic():
                total_jobs_processed = 0
                jobs_results = []
                
                for job_data in assignments_data:
                    job_result = self._process_single_job(job_data)
                    
                    # Si il y a des erreurs, arrêter immédiatement
                    if job_result['errors']:
                        error_msg = f"Erreur pour le job {job_result['job_id']}: {', '.join(job_result['errors'])}"
                        raise JobCreationError(error_msg)
                    
                    jobs_results.append(job_result)
                    total_jobs_processed += 1
                
                return {
                    'success': True,
                    'message': f'Traitement terminé pour {total_jobs_processed} jobs',
                    'total_jobs_processed': total_jobs_processed,
                    'jobs_results': jobs_results,
                    'processing_date': timezone.now()
                }
        except JobCreationError:
            # Re-raise les erreurs métier
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'affectation en lot: {str(e)}", exc_info=True)
            raise JobCreationError(f"Erreur lors de l'affectation en lot: {str(e)}")

    def _process_single_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        job_id = job_data['job_id']
        job_reference = None
        assignments_created = 0
        assignments_updated = 0
        resources_created = 0
        resources_updated = 0
        errors = []
        
        try:
            job = Job.objects.get(id=job_id)
            job_reference = job.reference
            
            # Affecter le 1er comptage si fourni
            team1 = job_data.get('team1')
            date1 = job_data.get('date1')
            if team1 is not None and isinstance(team1, int) and team1 > 0:
                try:
                    result = self.assignment_service.assign_jobs({
                        'job_ids': [job_id],
                        'counting_order': 1,
                        'session_id': team1,
                        'date_start': date1 or timezone.now()
                    })
                    assignments_created += result.get('assignments_created', 0)
                    assignments_updated += result.get('assignments_updated', 0)
                except Exception as e:
                    errors.append(f"Erreur affectation team1: {str(e)}")
            elif team1 is not None:
                errors.append(f"team1 invalide: {team1} (doit être un nombre positif)")
            
            # Affecter le 2ème comptage si fourni
            team2 = job_data.get('team2')
            date2 = job_data.get('date2')
            if team2 is not None and isinstance(team2, int) and team2 > 0:
                try:
                    result = self.assignment_service.assign_jobs({
                        'job_ids': [job_id],
                        'counting_order': 2,
                        'session_id': team2,
                        'date_start': date2 or timezone.now()
                    })
                    assignments_created += result.get('assignments_created', 0)
                    assignments_updated += result.get('assignments_updated', 0)
                except Exception as e:
                    errors.append(f"Erreur affectation team2: {str(e)}")
            elif team2 is not None:
                errors.append(f"team2 invalide: {team2} (doit être un nombre positif)")
            
            # Affecter les ressources si fournies
            resources_ids = job_data.get('resources', [])
            if resources_ids:
                # Valider que tous les IDs de ressources sont valides
                valid_resource_ids = []
                for resource_id in resources_ids:
                    if isinstance(resource_id, int) and resource_id > 0:
                        valid_resource_ids.append(resource_id)
                    else:
                        errors.append(f"Ressource ID invalide: {resource_id}")
                
                if valid_resource_ids:
                    try:
                        result = self.resource_assignment_service.assign_resources_to_job({
                            'job_id': job_id,
                            'resource_ids': valid_resource_ids
                        })
                        resources_created += result.get('assignments_created', 0)
                        resources_updated += result.get('assignments_updated', 0)
                    except Exception as e:
                        errors.append(f"Erreur affectation ressources: {str(e)}")
            
            return {
                'job_id': job_id,
                'job_reference': job_reference,
                'assignments_created': assignments_created,
                'assignments_updated': assignments_updated,
                'resources_created': resources_created,
                'resources_updated': resources_updated,
                'errors': errors
            }
            
        except Job.DoesNotExist:
            errors.append(f"Job avec l'ID {job_id} non trouvé")
            return {
                'job_id': job_id,
                'job_reference': job_reference,
                'assignments_created': 0,
                'assignments_updated': 0,
                'resources_created': 0,
                'resources_updated': 0,
                'errors': errors
            }
        except Exception as e:
            errors.append(f"Erreur inattendue: {str(e)}")
            return {
                'job_id': job_id,
                'job_reference': job_reference,
                'assignments_created': 0,
                'assignments_updated': 0,
                'resources_created': 0,
                'resources_updated': 0,
                'errors': errors
            } 