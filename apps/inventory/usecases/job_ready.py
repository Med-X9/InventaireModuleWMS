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
    Si counting_order est None, tous les comptages seront marqués comme PRET
    """
    
    def __init__(self):
        pass
    
    def execute(self, job_ids: List[int], counting_order: Optional[int] = None) -> Dict[str, Any]:
        """
        Marque plusieurs jobs et le comptage spécifié par ordre comme PRET
        Si counting_order est None, tous les comptages (1, 2, 3) seront marqués comme PRET
        
        Args:
            job_ids: Liste des IDs des jobs à marquer comme PRET
            counting_order: Ordre du comptage (1, 2 ou 3) à marquer comme PRET. Si None, tous les comptages seront traités
            
        Returns:
            Dict[str, Any]: Résultat du traitement avec la liste des jobs traités
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        try:
            with transaction.atomic():
                # Récupérer les jobs existants (ignorer ceux qui n'existent pas)
                jobs = Job.objects.filter(id__in=job_ids)
                
                # Déterminer les ordres de comptage à traiter
                if counting_order is None:
                    # Si counting_order n'est pas fourni, traiter tous les comptages (1, 2, 3)
                    counting_orders = [1, 2, 3]
                else:
                    # Sinon, traiter uniquement le comptage spécifié
                    counting_orders = [counting_order]
                
                # Valider et collecter tous les jobs/comptages valides (sans lever d'erreurs)
                validated_data = []  # Liste des tuples (job, counting, assignment, order) validés
                rejection_reasons = []  # Liste des raisons de rejet pour le diagnostic
                
                for job in jobs:
                    # Ignorer les jobs qui ne sont pas au statut AFFECTE ou PRET
                    # (permet un traitement progressif : le job peut déjà être PRET si un comptage précédent a été traité)
                    if job.status not in ['AFFECTE', 'PRET']:
                        reason = f"Job {job.reference} (ID: {job.id}) : statut actuel '{job.status}' (attendu: 'AFFECTE' ou 'PRET')"
                        logger.debug(reason)
                        rejection_reasons.append(reason)
                        continue
                    
                    # Vérifier que tous les assignments de ce job sont soit AFFECTE soit PRET
                    # (permet un traitement progressif : certains peuvent déjà être PRET)
                    all_assignments = Assigment.objects.filter(job=job)
                    assignments_invalid_status = all_assignments.exclude(status__in=['AFFECTE', 'PRET'])
                    
                    if assignments_invalid_status.exists():
                        # Récupérer les références des assignments avec statut invalide pour le log
                        invalid_status_refs = [
                            f"{ass.reference} (statut: {ass.status})" 
                            for ass in assignments_invalid_status.select_related('counting')
                        ]
                        reason = (
                            f"Job {job.reference} (ID: {job.id}) : tous les assignments doivent avoir le statut AFFECTE ou PRET. "
                            f"Assignments avec statut invalide: {', '.join(invalid_status_refs)}"
                        )
                        logger.warning(reason)
                        rejection_reasons.append(reason)
                        continue
                    
                    # Traiter chaque ordre de comptage
                    for order in counting_orders:
                        # Ignorer si le comptage n'existe pas
                        try:
                            counting = Counting.objects.get(inventory=job.inventory, order=order)
                        except Counting.DoesNotExist:
                            reason = (
                                f"Job {job.reference} (ID: {job.id}) : comptage d'ordre {order} n'existe pas "
                                f"pour l'inventaire {job.inventory.reference}"
                            )
                            logger.debug(reason)
                            rejection_reasons.append(reason)
                            continue
                        
                        # Ignorer si l'affectation n'existe pas
                        try:
                            assignment = Assigment.objects.get(job=job, counting=counting)
                        except Assigment.DoesNotExist:
                            reason = (
                                f"Job {job.reference} (ID: {job.id}) : aucune affectation trouvée "
                                f"pour le comptage d'ordre {order} (référence: {counting.reference})"
                            )
                            logger.debug(reason)
                            rejection_reasons.append(reason)
                            continue
                        
                        # Ignorer si l'affectation est déjà en PRET
                        if assignment.status == 'PRET':
                            reason = (
                                f"Job {job.reference} (ID: {job.id}) : affectation déjà en PRET "
                                f"pour le comptage d'ordre {order}"
                            )
                            logger.debug(reason)
                            rejection_reasons.append(reason)
                            continue
                        
                        # Ignorer si le comptage est "image de stock"
                        if counting.count_mode == "image de stock":
                            reason = (
                                f"Job {job.reference} (ID: {job.id}) : comptage d'ordre {order} "
                                f"avec mode 'image de stock' ignoré"
                            )
                            logger.debug(reason)
                            rejection_reasons.append(reason)
                            continue
                        
                        # Ignorer si l'affectation n'a pas de session
                        if assignment.session is None:
                            reason = (
                                f"Job {job.reference} (ID: {job.id}) : affectation sans session "
                                f"pour le comptage d'ordre {order}"
                            )
                            logger.debug(reason)
                            rejection_reasons.append(reason)
                            continue
                        
                        # Ignorer si l'affectation n'a pas le statut AFFECTE
                        if assignment.status != 'AFFECTE':
                            reason = (
                                f"Job {job.reference} (ID: {job.id}) : affectation avec statut '{assignment.status}' "
                                f"pour le comptage d'ordre {order} (attendu: 'AFFECTE')"
                            )
                            logger.debug(reason)
                            rejection_reasons.append(reason)
                            continue
                        
                        # Toutes les validations sont passées pour ce job et ce comptage
                        validated_data.append((job, counting, assignment, order))
                
                # Si aucun job/comptage valide n'a été trouvé, retourner un succès avec 0 jobs traités
                if not validated_data:
                    if counting_order is None:
                        message = "Aucun job/comptage valide trouvé pour être marqué comme PRET"
                    else:
                        message = (
                            f"Aucun job/comptage valide trouvé pour être marqué comme PRET "
                            f"pour le comptage d'ordre {counting_order}"
                        )
                    
                    # Ajouter les raisons de rejet si disponibles
                    response_data = {
                        'message': message,
                        'counting_order': counting_order,
                        'jobs_processed': 0,
                        'jobs': []
                    }
                    
                    if rejection_reasons:
                        response_data['rejection_reasons'] = rejection_reasons
                        response_data['total_rejections'] = len(rejection_reasons)
                    
                    return response_data
                
                # Mettre en PRET tous les jobs/comptages validés
                current_time = timezone.now()
                updated_jobs = []
                processed_jobs = set()  # Pour éviter de traiter plusieurs fois le même job
                
                for job, counting, assignment, order in validated_data:
                    logger.info(
                        f"Marquage du job {job.reference} (ID: {job.id}) "
                        f"et du comptage d'ordre {order} ({counting.reference}) comme PRET"
                    )
                    
                    # Marquer le job comme PRET (si ce n'est pas déjà fait par un autre comptage)
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
                    
                    # Ajouter le job avec ses informations de comptage
                    job_entry = next(
                        (j for j in updated_jobs if j.get('job_reference') == job.reference),
                        None
                    )
                    if job_entry:
                        # Ajouter ce comptage à la liste des comptages traités pour ce job
                        if 'counting_orders' not in job_entry:
                            job_entry['counting_orders'] = []
                        job_entry['counting_orders'].append({
                            'order': order,
                            'counting_reference': counting.reference
                        })
                    else:
                        # Créer une nouvelle entrée pour ce job
                        job_data = {
                            'job_reference': job.reference,
                            'counting_reference': counting.reference
                        }
                        if counting_order is None:
                            # Si on traite tous les comptages, créer une liste
                            job_data['counting_orders'] = [{
                                'order': order,
                                'counting_reference': counting.reference
                            }]
                        else:
                            # Si on traite un seul comptage, utiliser counting_order
                            job_data['counting_order'] = order
                        updated_jobs.append(job_data)
                    
                    logger.info(
                        f"Job {job.reference} marqué comme PRET "
                        f"(comptage: {counting.reference}, ordre: {order})"
                    )
                
                # Construire le message de retour
                if counting_order is None:
                    message = (
                        f"{len(updated_jobs)} job(s) "
                        f"marqué(s) comme PRET avec succès pour tous les comptages valides"
                    )
                else:
                    message = (
                        f"{len(updated_jobs)} job(s) "
                        f"marqué(s) comme PRET avec succès pour le comptage d'ordre {counting_order}"
                    )
                
                return {
                    'message': message,
                    'counting_order': counting_order,
                    'jobs_processed': len(updated_jobs),
                    'jobs': updated_jobs
                }
                
        except JobCreationError:
            raise
        except Exception as e:
            counting_order_str = "tous les comptages" if counting_order is None else f"le comptage d'ordre {counting_order}"
            logger.error(
                f"Erreur inattendue lors de la mise en prêt des jobs {job_ids} "
                f"et de {counting_order_str}: {str(e)}",
                exc_info=True
            )
            raise JobCreationError(
                f"Erreur inattendue lors de la mise en prêt des jobs {job_ids} "
                f"et de {counting_order_str}: {str(e)}"
            ) 