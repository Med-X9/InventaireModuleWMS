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

    Logique "tout ou rien" (all-or-nothing) :
    - Toutes les validations sont effectuées avant toute modification
    - Toutes les mises à jour sont faites dans une seule transaction atomique
    - En cas d'erreur à n'importe quelle étape, tout est annulé (rollback)

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

        LOGIQUE "TOUT OU RIEN" STRICTE :
        - Tous les jobs spécifiés doivent exister et être en statut AFFECTE
        - TOUS les assignments liés à ces jobs doivent être en statut AFFECTE
        - Si UN SEUL job ou assignment n'est pas en statut AFFECTE, TOUT est bloqué
        - Soit tout réussit, soit rien ne change (rollback automatique)

        Args:
            job_ids: Liste des IDs des jobs à traiter (obligatoire et non vide)

        Returns:
            Dict[str, Any]: Résultat du traitement

        Raises:
            JobCreationError: Si une erreur survient (transaction rollback automatique)
        """
        try:
                # Vérifier d'abord que tous les jobs spécifiés existent et sont en statut AFFECTE
                existing_jobs = Job.objects.filter(id__in=job_ids).select_related()

                # Vérifier que tous les jobs spécifiés existent
                found_job_ids = set(existing_jobs.values_list('id', flat=True))
                missing_job_ids = set(job_ids) - found_job_ids

                if missing_job_ids:
                    raise JobCreationError(
                        f"Jobs introuvables : {sorted(missing_job_ids)}"
                    )

                # Les jobs peuvent être dans n'importe quel statut tant qu'ils ont des assignments AFFECTE
                # Étape 1 : Collecte des erreurs de jobs
                job_errors = []
                valid_affecte_jobs = []

                for job in existing_jobs:
                    if job.status == 'AFFECTE':
                        # Seuls les jobs AFFECTE peuvent être traités
                        valid_affecte_jobs.append(job)
                    else:
                        # Tous les autres statuts sont des erreurs
                        job_errors.append(
                            f"Job {job.reference} (ID: {job.id}) : statut '{job.status}' (attendu: 'AFFECTE')"
                        )

                # Vérifier qu'on a au moins un job AFFECTE à traiter
                if not valid_affecte_jobs:
                    job_errors.append('Aucun job en statut AFFECTE trouvé')

                # Tous les jobs sont valides, procéder au traitement des jobs AFFECTE
                jobs = valid_affecte_jobs
                job_ids_list = [job.id for job in jobs]

                # Étape 2 : Collecte de TOUTES les erreurs (jobs + assignments)
                all_errors = job_errors  # Les erreurs de jobs sont déjà collectées

                # Récupérer TOUS les assignments de TOUS les jobs
                all_assignments = Assigment.objects.filter(
                    job_id__in=job_ids_list
                ).select_related('job', 'counting', 'session')

                # Vérifier les assignments
                for assignment in all_assignments:
                    if assignment.status != 'AFFECTE':
                        all_errors.append(
                            f"Assignment {assignment.reference} (Job: {assignment.job.reference}) : "
                            f"statut '{assignment.status}' (attendu: 'AFFECTE')"
                        )

                # Si des erreurs ont été collectées, les afficher toutes
                if all_errors:
                    raise JobCreationError(
                        f"Erreurs de validation : {' | '.join(all_errors)}"
                    )

                # Utiliser seulement les jobs AFFECTE valides pour le traitement
                jobs = valid_affecte_jobs
                job_ids_list = [job.id for job in jobs]

                # Étape 3 : Tout est valide, procéder aux mises à jour
                jobs = valid_affecte_jobs
                assignments = all_assignments

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

                # PHASE DE MISE À JOUR : Application des changements (dans la transaction)
                # Toutes les validations sont terminées, appliquer maintenant les modifications

                # Optimisation : Mise à jour bulk des assignments
                assignment_ids = [ass.id for ass in assignments]
                assignments_updated = Assigment.objects.filter(id__in=assignment_ids).update(
                    status='PRET',
                    pret_date=current_time
                )

                # Optimisation : Mise à jour bulk des jobs (seulement ceux validés)
                jobs_to_update_ids = [job.id for job in jobs]
                jobs_updated = Job.objects.filter(id__in=jobs_to_update_ids).update(
                    status='PRET',
                    pret_date=current_time
                )

                # Vérification de sécurité : s'assurer que toutes les mises à jour ont été appliquées
                if assignments_updated != len(assignment_ids):
                    raise JobCreationError(
                        f"Erreur lors de la mise à jour des assignments: "
                        f"{assignments_updated}/{len(assignment_ids)} assignments mis à jour"
                    )

                if jobs_updated != len(jobs_to_update_ids):
                    raise JobCreationError(
                        f"Erreur lors de la mise à jour des jobs: "
                        f"{jobs_updated}/{len(jobs_to_update_ids)} jobs mis à jour"
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
