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
            # Vérifier que le job existe
            job = Job.objects.get(id=job_id)
            job_reference = job.reference
            
            # Vérifier que le job n'est pas en statut 'EN ATTENTE'
            if job.status == 'EN ATTENTE':
                errors.append(f"Le job {job_reference} est en statut 'EN ATTENTE' et ne peut pas être affecté. Il doit d'abord être validé.")
                return {
                    'job_id': job_id,
                    'job_reference': job_reference,
                    'assignments_created': 0,
                    'assignments_updated': 0,
                    'resources_created': 0,
                    'resources_updated': 0,
                    'errors': errors
                }
            
            # Affecter tous les teams fournis (team1, team2, team3, team4, etc.)
            # Note: Le service AssignmentService gère automatiquement :
            # - Vérification que le job existe et appartient au bon inventaire
            # - Rejet des jobs en statut 'EN ATTENTE'
            # - Récupération du comptage selon counting_order et inventory_id
            # - Vérification si une session peut être affectée (selon le mode de comptage)
            # - Préservation des statuts 'PRET', 'TRANSFERT', 'ENTAME', 'TERMINE' pour les jobs et assignments
            # - Dans la réaffectation, le statut du job n'est pas modifié s'il est 'PRET', 'TRANSFERT', 'ENTAME' ou 'TERMINE'
            teams = job_data.get('teams', {})
            
            # Traiter chaque team dans l'ordre
            for team_num in sorted(teams.keys()):
                team_info = teams[team_num]
                session_id = team_info.get('session_id')
                counting_order = team_info.get('counting_order', team_num)
                date_start = team_info.get('date')
                
                if session_id is not None:
                    if not isinstance(session_id, int) or session_id <= 0:
                        errors.append(f"team{team_num} invalide: {session_id} (doit être un nombre positif)")
                        continue
                    
                    try:
                        result = self.assignment_service.assign_jobs({
                            'job_ids': [job_id],
                            'counting_order': counting_order,
                            'session_id': session_id,
                            'date_start': date_start or timezone.now()
                        })
                        assignments_created += result.get('assignments_created', 0)
                        assignments_updated += result.get('assignments_updated', 0)
                    except Exception as e:
                        errors.append(f"Erreur affectation team{team_num} (comptage {counting_order}): {str(e)}")
            
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
                        # Convertir la liste d'IDs en liste d'objets avec resource_id et quantity
                        resource_assignments = [
                            {'resource_id': resource_id, 'quantity': 1} 
                            for resource_id in valid_resource_ids
                        ]
                        
                        result = self.resource_assignment_service.assign_resources_to_job({
                            'job_id': job_id,
                            'resource_assignments': resource_assignments
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