"""
Use case pour mettre les jobs et leurs assignments en statut PRET
avec optimisation de performance
"""
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from ..models import Job, Assigment
from ..exceptions import JobCreationError
import logging

logger = logging.getLogger(__name__)


class JobSetReadyUseCase:
    """
    Use case pour mettre les jobs et leurs assignments en statut PRET

    Optimisations de performance :
    - Utilise des requêtes bulk pour les mises à jour
    - Évite les boucles individuelles save()
    - Utilise select_related/prefetch_related pour optimiser les requêtes
    """

    def __init__(self):
        pass

    def execute(self, job_ids: List[int]) -> Dict[str, Any]:
        """
        Met les jobs et leurs assignments en statut PRET

        Args:
            job_ids: Liste des IDs des jobs à traiter (obligatoire et non vide)

        Returns:
            Dict[str, Any]: Résultat du traitement

        Raises:
            JobCreationError: Si une erreur survient
        """
        try:
            with transaction.atomic():
                # Vérifier d'abord que tous les jobs spécifiés existent et sont en statut AFFECTE
                existing_jobs = Job.objects.filter(id__in=job_ids).select_related()

                # Vérifier que tous les jobs spécifiés existent
                found_job_ids = set(existing_jobs.values_list('id', flat=True))
                missing_job_ids = set(job_ids) - found_job_ids

                if missing_job_ids:
                    raise JobCreationError(
                        f"Jobs introuvables : {sorted(missing_job_ids)}"
                    )

                # Vérifier que tous les jobs sont en statut AFFECTE
                invalid_jobs = []
                for job in existing_jobs:
                    if job.status != 'AFFECTE':
                        invalid_jobs.append({
                            'id': job.id,
                            'reference': job.reference,
                            'current_status': job.status
                        })

                if invalid_jobs:
                    error_details = [
                        f"Job {job['reference']} (ID: {job['id']}) : statut '{job['current_status']}' (attendu: 'AFFECTE')"
                        for job in invalid_jobs
                    ]
                    raise JobCreationError(
                        f"Tous les jobs doivent être en statut AFFECTE. Jobs invalides : {' | '.join(error_details)}"
                    )

                # Tous les jobs sont valides, procéder au traitement
                jobs = existing_jobs

                # Récupérer les jobs et leurs assignments en une seule requête optimisée
                job_ids_list = list(jobs.values_list('id', flat=True))

                # Récupérer tous les assignments AFFECTE pour ces jobs
                assignments = Assigment.objects.filter(
                    job_id__in=job_ids_list,
                    status='AFFECTE'
                ).select_related('job', 'counting', 'session')

                if not assignments.exists():
                    return {
                        'message': 'Aucun assignment éligible trouvé (statut doit être AFFECTE)',
                        'jobs_processed': 0,
                        'assignments_processed': 0,
                        'jobs': []
                    }

                current_time = timezone.now()

                # Collecter les données pour la réponse avant les mises à jour
                jobs_data = []
                job_assignments_map = {}

                for assignment in assignments:
                    job_ref = assignment.job.reference
                    if job_ref not in job_assignments_map:
                        job_assignments_map[job_ref] = {
                            'job_id': assignment.job.id,
                            'assignments': []
                        }
                    job_assignments_map[job_ref]['assignments'].append({
                        'assignment_reference': assignment.reference,
                        'counting_reference': assignment.counting.reference if assignment.counting else None
                    })

                # Créer la liste des jobs pour la réponse
                for job_ref, data in job_assignments_map.items():
                    jobs_data.append({
                        'job_reference': job_ref,
                        'assignments_count': len(data['assignments']),
                        'assignments': data['assignments']
                    })

                # Optimisation : Mise à jour bulk des assignments
                assignment_ids = list(assignments.values_list('id', flat=True))
                Assigment.objects.filter(id__in=assignment_ids).update(
                    status='PRET',
                    pret_date=current_time
                )

                # Optimisation : Mise à jour bulk des jobs
                Job.objects.filter(id__in=job_ids_list).update(
                    status='PRET',
                    pret_date=current_time
                )

                # Log des opérations
                logger.info(
                    f"Mise en PRET de {len(jobs_data)} job(s) "
                    f"et {len(assignments)} assignment(s) effectuée"
                )

                return {
                    'message': f"{len(jobs_data)} job(s) et {len(assignments)} assignment(s) "
                              f"marqué(s) comme PRET avec succès",
                    'jobs_processed': len(jobs_data),
                    'assignments_processed': len(assignments),
                    'jobs': jobs_data
                }

        except Exception as e:
            logger.error(
                f"Erreur lors de la mise en PRET des jobs: {str(e)}",
                exc_info=True
            )
            raise JobCreationError(
                f"Erreur lors de la mise en PRET des jobs: {str(e)}"
            )
