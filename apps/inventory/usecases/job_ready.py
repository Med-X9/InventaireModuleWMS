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
                
                for job in jobs:
                    # Ignorer les jobs qui n'ont pas le statut AFFECTE
                    if job.status != 'AFFECTE':
                        logger.debug(
                            f"Job {job.reference} (ID: {job.id}) ignoré - statut actuel : {job.status} "
                            f"(attendu: AFFECTE)"
                        )
                        continue
                    
                    # Traiter chaque ordre de comptage
                    for order in counting_orders:
                        # Ignorer si le comptage n'existe pas
                        try:
                            counting = Counting.objects.get(inventory=job.inventory, order=order)
                        except Counting.DoesNotExist:
                            logger.debug(
                                f"Comptage d'ordre {order} ignoré pour l'inventaire "
                                f"{job.inventory.reference} (ID: {job.inventory.id}) du job {job.reference} (ID: {job.id})"
                            )
                            continue
                        
                        # Ignorer si l'affectation n'existe pas
                        try:
                            assignment = Assigment.objects.get(job=job, counting=counting)
                        except Assigment.DoesNotExist:
                            logger.debug(
                                f"Affectation ignorée pour le job {job.reference} (ID: {job.id}) "
                                f"et le comptage d'ordre {order} (référence: {counting.reference})"
                            )
                            continue
                        
                        # Ignorer si l'affectation est déjà en PRET
                        if assignment.status == 'PRET':
                            logger.debug(
                                f"Affectation déjà en PRET pour le job {job.reference} (ID: {job.id}) "
                                f"et le comptage d'ordre {order}"
                            )
                            continue
                        
                        # Ignorer si le comptage est "image de stock"
                        if counting.count_mode == "image de stock":
                            logger.debug(
                                f"Comptage d'ordre {order} avec mode 'image de stock' ignoré "
                                f"pour le job {job.reference} (ID: {job.id})"
                            )
                            continue
                        
                        # Ignorer si l'affectation n'a pas de session
                        if assignment.session is None:
                            logger.debug(
                                f"Affectation sans session ignorée pour le job {job.reference} (ID: {job.id}) "
                                f"et le comptage d'ordre {order}"
                            )
                            continue
                        
                        # Ignorer si l'affectation n'a pas le statut AFFECTE
                        if assignment.status != 'AFFECTE':
                            logger.debug(
                                f"Affectation avec statut {assignment.status} ignorée pour le job {job.reference} (ID: {job.id}) "
                                f"et le comptage d'ordre {order} (attendu: AFFECTE)"
                            )
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
                    return {
                        'message': message,
                        'counting_order': counting_order,
                        'jobs_processed': 0,
                        'jobs': []
                    }
                
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