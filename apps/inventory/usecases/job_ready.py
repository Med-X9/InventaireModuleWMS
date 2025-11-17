"""
Use case pour marquer plusieurs jobs et un comptage spécifique comme PRET
"""
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from ..models import Job, Assigment, Counting
from ..exceptions import JobCreationError
import logging

logger = logging.getLogger(__name__)

class JobReadyUseCase:
    """
    Use case pour marquer plusieurs jobs et un comptage spécifique (par ordre) comme PRET
    """
    
    def __init__(self):
        pass
    
    def execute(self, job_ids: List[int], counting_order: Optional[int] = None) -> Dict[str, Any]:
        """
        Marque plusieurs jobs et le comptage spécifié par ordre comme PRET
        
        Args:
            job_ids: Liste des IDs des jobs à marquer comme PRET
            counting_order: Ordre du comptage (1, 2 ou 3) à marquer comme PRET. 
                            Si None, tous les comptages des jobs seront marqués comme PRET
            
        Returns:
            Dict[str, Any]: Résultat du traitement avec la liste des jobs traités
            
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
                
                # Vérifier que tous les jobs appartiennent au même inventaire (si nécessaire)
                # Pour simplifier, on permet différents inventaires, mais on vérifie que chaque inventaire a le comptage
                
                # Valider tous les jobs avant de commencer les mises à jour
                errors = []
                validated_data = []  # Liste des tuples (job, counting, assignment) validés
                
                for job in jobs:
                    # Vérifier que le job a le statut AFFECTE
                    if job.status != 'AFFECTE':
                        errors.append(
                            f"Job {job.reference} (ID: {job.id}) doit avoir le statut AFFECTE. "
                            f"Statut actuel : {job.status}"
                        )
                        continue
                    
                    # Si counting_order est None, traiter tous les comptages du job
                    if counting_order is None:
                        # Récupérer toutes les affectations du job avec statut AFFECTE
                        assignments = Assigment.objects.filter(
                            job=job,
                            status='AFFECTE'
                        ).select_related('counting')
                        
                        if not assignments.exists():
                            errors.append(
                                f"Aucune affectation en statut AFFECTE trouvée pour le job {job.reference} (ID: {job.id})"
                            )
                            continue
                        
                        for assignment in assignments:
                            counting = assignment.counting
                            
                            # Vérifier que l'affectation n'est pas déjà en PRET
                            if assignment.status == 'PRET':
                                continue  # Ignorer les affectations déjà en PRET
                            
                            # Cas spécial : Si le comptage est "image de stock", il ne peut pas être mis en PRET
                            if counting.count_mode == "image de stock":
                                continue  # Ignorer les comptages "image de stock"
                            
                            # Vérifier que l'affectation a une session (doit être affectée)
                            if assignment.session is None:
                                continue  # Ignorer les affectations sans session
                            
                            # Toutes les validations sont passées pour cette affectation
                            validated_data.append((job, counting, assignment))
                    else:
                        # Comportement original : traiter un comptage spécifique
                        # Vérifier que le comptage existe pour cet inventaire et cet ordre
                        try:
                            counting = Counting.objects.get(inventory=job.inventory, order=counting_order)
                        except Counting.DoesNotExist:
                            errors.append(
                                f"Comptage d'ordre {counting_order} non trouvé pour l'inventaire "
                                f"{job.inventory.reference} (ID: {job.inventory.id}) du job {job.reference} (ID: {job.id})"
                            )
                            continue
                        
                        # Vérifier qu'une affectation existe pour ce job et ce comptage
                        try:
                            assignment = Assigment.objects.get(job=job, counting=counting)
                        except Assigment.DoesNotExist:
                            errors.append(
                                f"Aucune affectation trouvée pour le job {job.reference} (ID: {job.id}) "
                                f"et le comptage d'ordre {counting_order} (référence: {counting.reference})"
                            )
                            continue
                        
                        # Vérifier que l'affectation n'est pas déjà en PRET
                        if assignment.status == 'PRET':
                            errors.append(
                                f"L'affectation pour le job {job.reference} (ID: {job.id}) "
                                f"et le comptage d'ordre {counting_order} est déjà au statut PRET"
                            )
                            continue
                        
                        # Cas spécial : Si le comptage est "image de stock", il ne peut pas être mis en PRET
                        if counting.count_mode == "image de stock":
                            errors.append(
                                f"Le comptage d'ordre {counting_order} avec le mode 'image de stock' "
                                f"ne peut pas être mis au statut PRET pour le job {job.reference} (ID: {job.id}). "
                                f"Seuls les comptages avec session affectée peuvent être mis en PRET."
                            )
                            continue
                        
                        # Vérifier que l'affectation a une session (doit être affectée)
                        if assignment.session is None:
                            errors.append(
                                f"L'affectation pour le job {job.reference} (ID: {job.id}) "
                                f"et le comptage d'ordre {counting_order} n'a pas de session affectée. "
                                f"Seules les affectations avec session peuvent être mises au statut PRET."
                            )
                            continue
                        
                        # Vérifier que l'affectation a le statut AFFECTE
                        if assignment.status != 'AFFECTE':
                            errors.append(
                                f"L'affectation pour le job {job.reference} (ID: {job.id}) "
                                f"et le comptage d'ordre {counting_order} doit avoir le statut AFFECTE. "
                                f"Statut actuel : {assignment.status}"
                            )
                            continue
                        
                        # Toutes les validations sont passées pour ce job
                        validated_data.append((job, counting, assignment))
                
                # Si des erreurs existent, les lever
                if errors:
                    raise JobCreationError(
                        f"Erreurs de validation pour {len(errors)} job(s) sur {len(job_ids)} demandé(s). "
                        f"Détails : {' | '.join(errors)}"
                    )
                
                # Toutes les validations sont passées, mettre en PRET tous les jobs validés
                current_time = timezone.now()
                updated_jobs = []
                updated_assignments = []
                
                # Utiliser un set pour éviter de traiter plusieurs fois le même job
                processed_jobs = set()
                
                for job, counting, assignment in validated_data:
                    counting_order_display = counting.order if counting_order is None else counting_order
                    logger.info(
                        f"Marquage du job {job.reference} (ID: {job.id}) "
                        f"et du comptage d'ordre {counting.order} ({counting.reference}) comme PRET"
                    )
                    
                    # Marquer le job comme PRET (si ce n'est pas déjà fait par un autre comptage)
                    if job.id not in processed_jobs:
                        job.status = 'PRET'
                        if job.pret_date is None:
                            job.pret_date = current_time
                        job.save()
                        processed_jobs.add(job.id)
                        
                        updated_jobs.append({
                            'job_id': job.id,
                            'job_reference': job.reference
                        })
                    
                    # Marquer l'assignment comme PRET
                    assignment.status = 'PRET'
                    assignment.pret_date = current_time
                    assignment.save()
                    
                    updated_assignments.append({
                        'assignment_id': assignment.id,
                        'assignment_reference': assignment.reference,
                        'counting_reference': counting.reference,
                        'counting_order': counting.order
                    })
                    
                    logger.info(
                        f"Assignment {assignment.reference} marqué comme PRET "
                        f"(job: {job.reference}, comptage: {counting.reference}, ordre: {counting.order})"
                    )
                
                # Construire le message de retour
                if counting_order is None:
                    message = (
                        f"{len(updated_jobs)} job(s) et {len(updated_assignments)} affectation(s) "
                        f"marqué(s) comme PRET avec succès (tous les comptages)"
                    )
                else:
                    message = (
                        f"{len(updated_jobs)} job(s) et {len(updated_assignments)} affectation(s) "
                        f"marqué(s) comme PRET avec succès pour le comptage d'ordre {counting_order}"
                    )
                
                return {
                    'message': message,
                    'counting_order': counting_order,
                    'jobs_processed': len(updated_jobs),
                    'assignments_processed': len(updated_assignments),
                    'jobs': updated_jobs,
                    'assignments': updated_assignments
                }
                
        except JobCreationError:
            raise
        except Exception as e:
            counting_order_display = counting_order if counting_order is not None else "tous"
            logger.error(
                f"Erreur inattendue lors de la mise en prêt des jobs {job_ids} "
                f"et du comptage d'ordre {counting_order_display}: {str(e)}",
                exc_info=True
            )
            raise JobCreationError(
                f"Erreur inattendue lors de la mise en prêt des jobs {job_ids} "
                f"et du comptage d'ordre {counting_order_display}: {str(e)}"
            ) 