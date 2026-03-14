"""
Use case pour marquer tous les assignments d'un job comme PRET
"""
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from ..models import Job, Assigment
from ..exceptions import JobCreationError
import logging

logger = logging.getLogger(__name__)

class JobReadyUseCase:
    """
    Use case pour marquer tous les assignments d'un job (avec statut AFFECTE) comme PRET
    """
    
    def __init__(self):
        pass
    
    def execute(self, job_ids: List[int], counting_order: Optional[int] = None) -> Dict[str, Any]:
        """
        Marque tous les assignments avec statut AFFECTE des jobs spécifiés comme PRET
        
        Args:
            job_ids: Liste des IDs des jobs à marquer comme PRET
            counting_order: Paramètre ignoré (conservé pour rétrocompatibilité)
            
        Returns:
            Dict[str, Any]: Résultat du traitement avec la liste des jobs traités
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        try:
            with transaction.atomic():
                # Récupérer les jobs existants
                jobs = Job.objects.filter(id__in=job_ids)
                
                # Valider et collecter tous les jobs/assignments valides
                validated_data = []  # Liste des tuples (job, assignment) validés
                rejection_reasons = []  # Liste des raisons de rejet pour le diagnostic
                
                for job in jobs:
                    # Ignorer les jobs qui ne sont pas au statut AFFECTE
                    if job.status != 'AFFECTE':
                        reason = f"Job {job.reference} (ID: {job.id}) : statut actuel '{job.status}' (attendu: 'AFFECTE')"
                        logger.debug(reason)
                        rejection_reasons.append(reason)
                        continue
                    
                    # Récupérer tous les assignments du job avec statut AFFECTE
                    assignments = Assigment.objects.filter(job=job, status='AFFECTE')
                    
                    if not assignments.exists():
                        reason = (
                            f"Job {job.reference} (ID: {job.id}) : aucun assignment avec statut AFFECTE trouvé"
                        )
                        logger.debug(reason)
                        rejection_reasons.append(reason)
                        continue
                    
                    # Ajouter tous les assignments valides
                    for assignment in assignments:
                        # Vérifier que l'assignment a une session
                        if assignment.session is None:
                            reason = (
                                f"Job {job.reference} (ID: {job.id}) : assignment {assignment.reference} "
                                f"sans session ignoré"
                            )
                            logger.debug(reason)
                            rejection_reasons.append(reason)
                            continue
                        
                        # Toutes les validations sont passées pour ce job et cet assignment
                        validated_data.append((job, assignment))
                
                # Si aucun job/assignment valide n'a été trouvé, retourner un succès avec 0 jobs traités
                if not validated_data:
                    message = "Aucun job/assignment valide trouvé pour être marqué comme PRET"
                    
                    # Ajouter les raisons de rejet si disponibles
                    response_data = {
                        'message': message,
                        'jobs_processed': 0,
                        'jobs': []
                    }
                    
                    if rejection_reasons:
                        response_data['rejection_reasons'] = rejection_reasons
                        response_data['total_rejections'] = len(rejection_reasons)
                    
                    return response_data
                
                # Mettre en PRET tous les jobs/assignments validés
                current_time = timezone.now()
                updated_jobs = []
                processed_jobs = set()  # Pour éviter de traiter plusieurs fois le même job
                
                for job, assignment in validated_data:
                    logger.info(
                        f"Marquage du job {job.reference} (ID: {job.id}) "
                        f"et de l'assignment {assignment.reference} comme PRET"
                    )
                    
                    # Marquer le job comme PRET (si ce n'est pas déjà fait)
                    if job.id not in processed_jobs:
                        job.status = 'PRET'
                        if job.pret_date is None:
                            job.pret_date = current_time
                        job.save()
                        processed_jobs.add(job.id)
                    
                    # Marquer l'assignment comme PRET
                    assignment.status = 'PRET'
                    assignment.pret_date = current_time
                    assignment.save()
                    
                    # Ajouter le job avec ses informations d'assignment
                    job_entry = next(
                        (j for j in updated_jobs if j.get('job_reference') == job.reference),
                        None
                    )
                    if job_entry:
                        # Ajouter cet assignment à la liste des assignments traités pour ce job
                        if 'assignments' not in job_entry:
                            job_entry['assignments'] = []
                        job_entry['assignments'].append({
                            'assignment_reference': assignment.reference,
                            'counting_reference': assignment.counting.reference if assignment.counting else None
                        })
                    else:
                        # Créer une nouvelle entrée pour ce job
                        job_data = {
                            'job_reference': job.reference,
                            'assignments': [{
                                'assignment_reference': assignment.reference,
                                'counting_reference': assignment.counting.reference if assignment.counting else None
                            }]
                        }
                        updated_jobs.append(job_data)
                    
                    logger.info(
                        f"Job {job.reference} marqué comme PRET "
                        f"(assignment: {assignment.reference})"
                    )
                
                # Construire le message de retour
                message = (
                    f"{len(updated_jobs)} job(s) "
                    f"marqué(s) comme PRET avec succès"
                )
                
                return {
                    'message': message,
                    'jobs_processed': len(updated_jobs),
                    'jobs': updated_jobs
                }
                
        except JobCreationError:
            raise
        except Exception as e:
            logger.error(
                f"Erreur inattendue lors de la mise en prêt des jobs {job_ids}: {str(e)}",
                exc_info=True
            )
            raise JobCreationError(
                f"Erreur inattendue lors de la mise en prêt des jobs {job_ids}: {str(e)}"
            ) 