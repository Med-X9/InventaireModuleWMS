"""
Service pour le lancement d'un nouveau comptage (3e et suivants) pour un job donné.
"""
from typing import Dict, Any, Optional

from django.db import transaction
from django.utils import timezone

from ..repositories.job_repository import JobRepository
from ..repositories.counting_repository import CountingRepository
from ..repositories.assignment_repository import AssignmentRepository
from ..models import JobDetail, Assigment
from ..exceptions.counting_exceptions import (
    CountingValidationError,
    CountingNotFoundError,
    CountingCreationError,
)
from apps.users.models import UserApp


class CountingLaunchService:
    """
    Service métier chargé de lancer un nouveau comptage pour un job.
    """

    def __init__(
        self,
        job_repository: Optional[JobRepository] = None,
        counting_repository: Optional[CountingRepository] = None,
        assignment_repository: Optional[AssignmentRepository] = None,
    ) -> None:
        self.job_repository = job_repository or JobRepository()
        self.counting_repository = counting_repository or CountingRepository()
        self.assignment_repository = assignment_repository or AssignmentRepository()

    @transaction.atomic
    def launch_counting(self, job_id: int, location_id: int, session_id: int) -> Dict[str, Any]:
        """
        Lance un comptage supplémentaire pour un job et un emplacement.

        Args:
            job_id: Identifiant du job ciblé.
            location_id: Identifiant de l'emplacement concerné.
            session_id: Identifiant de la session (équipe mobile) à affecter.

        Returns:
            Dict[str, Any]: Résultat détaillé du lancement.

        Raises:
            CountingValidationError: Données invalides ou incohérentes.
            CountingNotFoundError: Ressource inexistante (job, comptage, etc.).
            CountingCreationError: Erreur inattendue lors du traitement.
        """
        # Validation rapide des identifiants fournis
        if job_id <= 0:
            raise CountingValidationError("L'identifiant du job doit être strictement positif.")
        if location_id <= 0:
            raise CountingValidationError("L'identifiant de l'emplacement doit être strictement positif.")
        if session_id <= 0:
            raise CountingValidationError("L'identifiant de l'équipe doit être strictement positif.")

        try:
            # Étape 1 : récupérer les entités nécessaires
            job = self.job_repository.get_job_by_id(job_id)
            if not job:
                raise CountingNotFoundError(f"Job introuvable pour l'identifiant {job_id}.")

            location = self.job_repository.get_location_by_id(location_id)
            if not location:
                raise CountingValidationError(f"Emplacement introuvable pour l'identifiant {location_id}.")

            session = UserApp.objects.filter(id=session_id, type='Mobile').first()
            if not session:
                raise CountingValidationError("La session fournie n'existe pas ou n'est pas de type 'Mobile'.")

            # Vérification que l'emplacement est bien associé au job (au moins via un autre comptage)
            job_location_link = self.job_repository.get_job_detail_by_job_and_location(job, location)
            if not job_location_link:
                raise CountingValidationError(
                    "L'emplacement indiqué n'est pas affecté au job sélectionné."
                )

            # Étape 2 : récupérer le comptage de référence (ordre 3)
            counting_order_three = self.counting_repository.get_by_inventory_and_order(
                job.inventory_id,
                3,
            )
            if not counting_order_three:
                raise CountingNotFoundError(
                    f"Aucun comptage d'ordre 3 n'est défini pour l'inventaire {job.inventory_id}."
                )

            existing_assignment = self.assignment_repository.get_existing_assignment_for_job_and_counting(
                job.id,
                counting_order_three.id,
            )

            # Étape 3 : déterminer le comptage cible (3e ou duplication pour 4e, 5e, ...)
            new_counting_created = False
            if existing_assignment is None:
                self._ensure_previous_countings_completed(job.id, target_order=3)
                target_counting = counting_order_three
            else:
                next_order = self.counting_repository.get_next_order(job.inventory_id)
                self._ensure_previous_countings_completed(job.id, target_order=next_order)
                target_counting = self.counting_repository.duplicate_counting(counting_order_three.id)
                new_counting_created = True

            # Étape 4 : garantir l'existence du job detail pour ce comptage et cet emplacement
            job_detail = self.job_repository.get_job_detail_by_job_location_and_counting(
                job,
                location,
                target_counting,
            )
            job_detail_created = False
            if job_detail is None:
                job_detail = self.job_repository.create_job_detail(
                    reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                    location=location,
                    job=job,
                    counting=target_counting,
                    status='EN ATTENTE',
                )
                job_detail_created = True

            # Étape 5 : créer ou mettre à jour l'affectation correspondante
            assignment = self.assignment_repository.get_existing_assignment_for_job_and_counting(
                job.id,
                target_counting.id,
            )

            assignment_created = False
            current_time = timezone.now()
            if assignment is None:
                assignment = self.assignment_repository.create_assignment({
                    'reference': Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                    'job': job,
                    'counting': target_counting,
                    'session': session,
                    'status': 'TRANSFERT',
                    'date_start': current_time,
                    'affecte_date': current_time,
                    'pret_date': current_time,
                    'transfert_date': current_time,
                })
                assignment_created = True
            else:
                assignment.session = session
                assignment.status = 'TRANSFERT'
                assignment.date_start = current_time
                assignment.affecte_date = current_time
                assignment.pret_date = current_time
                assignment.transfert_date = current_time
                assignment.save()

            return {
                'job_id': job.id,
                'location_id': location.id,
                'counting': {
                    'id': target_counting.id,
                    'order': target_counting.order,
                    'reference': target_counting.reference,
                    'new_counting_created': new_counting_created,
                },
                'assignment': {
                    'id': assignment.id,
                    'status': assignment.status,
                    'session_id': session.id if session else None,
                    'created': assignment_created,
                },
                'job_detail': {
                    'id': job_detail.id,
                    'created': job_detail_created,
                },
                'timestamp': current_time,
            }
        except (CountingValidationError, CountingNotFoundError):
            # Ces exceptions sont attendues et doivent être relayées telles quelles.
            raise
        except Exception as exc:
            raise CountingCreationError(f"Erreur lors du lancement du comptage: {exc}") from exc

    def _ensure_previous_countings_completed(self, job_id: int, target_order: int) -> None:
        """
        Vérifie que les comptages nécessaires sont terminés avant de lancer le suivant.
        """
        if target_order == 3:
            required_orders = [1, 2]
        else:
            required_orders = [target_order - 1]

        for order in required_orders:
            assignment = self.assignment_repository.get_assignment_by_job_and_order(job_id, order)
            if assignment is None:
                if target_order == 3:
                    raise CountingValidationError(
                        "Impossible de lancer le 3ème comptage : les affectations des comptages 1 et 2 sont manquantes."
                    )
                raise CountingValidationError(
                    f"Impossible de lancer le comptage d'ordre {target_order} : aucune affectation trouvée pour le comptage d'ordre {order}."
                )

            if assignment.status != 'TERMINE':
                if target_order == 3:
                    raise CountingValidationError(
                        "Impossible de lancer le 3ème comptage tant que les comptages 1 et 2 ne sont pas terminés."
                    )
                raise CountingValidationError(
                    f"Impossible de lancer le comptage d'ordre {target_order} tant que le comptage d'ordre {order} n'est pas terminé."
                )

