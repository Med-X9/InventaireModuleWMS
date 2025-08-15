"""
Use case pour marquer les jobs et leurs comptages comme PRET
"""
from typing import List, Dict, Any
from django.db import transaction
from django.utils import timezone
from ..models import Job, Assigment, Counting
from ..exceptions import JobCreationError
import logging

logger = logging.getLogger(__name__)

class JobReadyUseCase:
    """
    Use case pour marquer les jobs et leurs comptages comme PRET
    """
    
    def __init__(self):
        pass
    
    def execute(self, job_ids: List[int]) -> Dict[str, Any]:
        """
        Marque les jobs et leurs comptages comme PRET
        
        Args:
            job_ids: Liste des IDs des jobs à marquer comme PRET
            
        Returns:
            Dict[str, Any]: Résultat du traitement
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        try:
            with transaction.atomic():
                # Vérifier que tous les jobs existent
                jobs = Job.objects.filter(id__in=job_ids)
                found_job_ids = set(job.id for job in jobs)
                requested_job_ids = set(job_ids)
                
                # Identifier les jobs qui n'existent pas
                missing_job_ids = requested_job_ids - found_job_ids
                if missing_job_ids:
                    missing_jobs_str = ', '.join(map(str, sorted(missing_job_ids)))
                    raise JobCreationError(f"Jobs non trouvés avec les IDs : {missing_jobs_str}")
                
                # Vérifier que tous les jobs ont le statut AFFECTE et que leurs comptages sont correctement affectés
                invalid_jobs = []
                for job in jobs:
                    if job.status != 'AFFECTE':
                        invalid_jobs.append(f"Job {job.reference} (statut: {job.status})")
                        continue
                    
                    # Vérifier que le job a au moins une affectation
                    job_assignments = Assigment.objects.filter(job=job)
                    if not job_assignments.exists():
                        invalid_jobs.append(f"Job {job.reference} (aucun comptage affecté)")
                        continue
                    
                    # Récupérer les comptages d'ordre 1 et 2 de l'inventaire
                    inventory_countings = Counting.objects.filter(inventory=job.inventory, order__in=[1, 2])
                    job_counting_ids = set(job_assignments.values_list('counting_id', flat=True))
                    inventory_counting_ids = set(inventory_countings.values_list('id', flat=True))
                    
                    # Vérifier la configuration des comptages
                    counting1 = inventory_countings.filter(order=1).first()
                    counting2 = inventory_countings.filter(order=2).first()
                    
                    if not counting1 or not counting2:
                        invalid_jobs.append(f"Job {job.reference} (comptages d'ordre 1 et 2 requis)")
                        continue
                    
                    # Vérifier que les assignments ont des sessions (sont affectés)
                    assignments_with_session = job_assignments.filter(session__isnull=False)
                    if not assignments_with_session.exists():
                        invalid_jobs.append(f"Job {job.reference} (aucun comptage avec session affectée)")
                        continue
                    
                    # Cas spécial : Si le 1er comptage est "image de stock", seul le 2ème comptage doit être affecté
                    if counting1.count_mode == "image de stock":
                        # Vérifier que le 2ème comptage est affecté avec une session
                        assignment2 = assignments_with_session.filter(counting=counting2).first()
                        if not assignment2:
                            invalid_jobs.append(f"Job {job.reference} (2ème comptage non affecté avec session alors que 1er est image de stock)")
                            continue
                        
                        # Vérifier que le 2ème comptage a une session (pas d'image de stock)
                        if assignment2.counting.count_mode == "image de stock":
                            invalid_jobs.append(f"Job {job.reference} (2ème comptage ne peut pas être image de stock)")
                            continue
                        
                        # Le 1er comptage (image de stock) n'a pas besoin d'être affecté avec une session
                        logger.info(f"Job {job.reference}: Configuration valide - 1er comptage image de stock, 2ème comptage affecté avec session")
                    
                    else:
                        # Cas normal : Vérifier que tous les comptages d'ordre 1 et 2 sont affectés avec des sessions
                        missing_countings = inventory_counting_ids - set(assignments_with_session.values_list('counting_id', flat=True))
                        if missing_countings:
                            missing_counting_refs = [f"comptage {cnt.reference}" for cnt in inventory_countings.filter(id__in=missing_countings)]
                            invalid_jobs.append(f"Job {job.reference} (comptages non affectés avec session: {', '.join(missing_counting_refs)})")
                
                if invalid_jobs:
                    raise JobCreationError(
                        f"Seuls les jobs avec le statut AFFECTE et leurs comptages correctement affectés avec des sessions peuvent être mis au statut PRET. "
                        f"Jobs invalides : {', '.join(invalid_jobs)}"
                    )
                
                # Marquer les jobs comme PRET
                current_time = timezone.now()
                updated_jobs = []
                updated_assignments = []
                
                for job in jobs:
                    logger.info(f"Marquage du job {job.reference} comme PRET")
                    
                    # Marquer le job comme PRET
                    job.status = 'PRET'
                    job.pret_date = current_time
                    job.save()
                    
                    updated_jobs.append({
                        'job_id': job.id,
                        'job_reference': job.reference
                    })
                    
                    # Marquer tous les assignments du job comme PRET
                    assignments = Assigment.objects.filter(job=job)
                    for assignment in assignments:
                        assignment.status = 'PRET'
                        assignment.pret_date = current_time
                        assignment.save()
                        updated_assignments.append({
                            'assignment_id': assignment.id,
                            'counting_reference': assignment.counting.reference,
                            'counting_order': assignment.counting.order
                        })
                        
                        logger.info(f"Assignment {assignment.reference} marqué comme PRET (comptage: {assignment.counting.reference})")
                
                return {
                    'message': f'{len(updated_jobs)} jobs et {len(updated_assignments)} assignments marqués comme PRET'
                }
                
        except JobCreationError:
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la mise en prêt des jobs: {str(e)}", exc_info=True)
            raise JobCreationError(f"Erreur inattendue lors de la mise en prêt des jobs: {str(e)}") 