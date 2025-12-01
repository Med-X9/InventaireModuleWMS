"""
Service pour le lancement d'un nouveau comptage (3e et suivants) pour un job donné.
"""
from typing import Dict, Any, Optional, List

from django.db import transaction
from django.utils import timezone

from ..repositories.job_repository import JobRepository
from ..repositories.counting_repository import CountingRepository
from ..repositories.assignment_repository import AssignmentRepository
from ..models import JobDetail, Assigment, EcartComptage, ComptageSequence, CountingDetail
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

            # Vérification métier supplémentaire :
            # Si un EcartComptage existe pour ce couple (job, emplacement) avec un résultat final
            # non nul ET marqué comme résolu, alors il est interdit de lancer un nouveau comptage.
            resolved_ecart_exists = EcartComptage.objects.filter(
                inventory=job.inventory,
                final_result__isnull=False,
                resolved=True,
                counting_sequences__counting_detail__job=job,
                counting_sequences__counting_detail__location=location,
            ).exists()

            if resolved_ecart_exists:
                raise CountingValidationError(
                    "Impossible de lancer un nouveau comptage : l'écart pour cet emplacement "
                    "est déjà résolu avec un résultat final."
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

            # Étape 3 : déterminer le comptage cible en trouvant le plus haut ordre avec JobDetail
            # Trouver le plus haut ordre de comptage pour lequel un JobDetail existe déjà pour cet emplacement
            highest_order_with_jobdetail = self._find_highest_counting_order_with_jobdetail(
                job, location
            )
            
            new_counting_created = False
            if highest_order_with_jobdetail is None or highest_order_with_jobdetail < 3:
                # Aucun JobDetail n'existe pour cet emplacement (ou seulement pour comptages 1-2)
                # → C'est le lancement du comptage 3
                self._ensure_previous_countings_completed(job.id, location.id, target_order=3)
                target_counting = counting_order_three
            else:
                # Un JobDetail existe déjà pour un comptage >= 3
                # → C'est un comptage supplémentaire (4, 5, etc.)
                # Le comptage cible est le suivant après le plus haut trouvé
                target_order = highest_order_with_jobdetail + 1
                self._ensure_previous_countings_completed(job.id, location.id, target_order=target_order)
                
                # Vérifier si le comptage cible existe déjà (créé par un autre emplacement)
                existing_target_counting = self.counting_repository.get_by_inventory_and_order(
                    job.inventory_id,
                    target_order,
                )
                
                if existing_target_counting:
                    # Le comptage existe déjà (créé pour un autre emplacement) → l'utiliser
                    target_counting = existing_target_counting
                else:
                    # Le comptage n'existe pas → le créer par duplication du comptage 3
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

    def _find_highest_counting_order_with_jobdetail(self, job, location) -> Optional[int]:
        """
        Trouve le plus haut ordre de comptage pour lequel un JobDetail existe
        pour ce job et cet emplacement.
        
        Args:
            job: L'objet Job
            location: L'objet Location
            
        Returns:
            L'ordre du comptage le plus élevé trouvé, ou None si aucun JobDetail n'existe
        """
        from ..models import JobDetail
        
        # Récupérer tous les JobDetails pour ce job et cet emplacement
        job_details = JobDetail.objects.filter(
            job=job,
            location=location
        ).select_related('counting').order_by('-counting__order')
        
        if not job_details.exists():
            return None
        
        # Retourner l'ordre du comptage le plus élevé
        highest_job_detail = job_details.first()
        if highest_job_detail and highest_job_detail.counting:
            return highest_job_detail.counting.order
        
        return None

    def _ensure_previous_countings_completed(self, job_id: int, location_id: int, target_order: int) -> None:
        """
        Vérifie que les comptages nécessaires sont terminés pour cet emplacement avant de lancer le suivant.
        
        Args:
            job_id: ID du job
            location_id: ID de l'emplacement pour lequel on vérifie
            target_order: Ordre du comptage à lancer (3, 4, 5, etc.)
        
        Raises:
            CountingValidationError: Si les comptages précédents ne sont pas terminés pour cet emplacement
        """
        # Déterminer les ordres de comptages à vérifier
        if target_order == 3:
            required_orders = [1, 2]
        else:
            required_orders = [target_order - 1]

        # Récupérer le job et l'emplacement
        job = self.job_repository.get_job_by_id(job_id)
        if not job:
            raise CountingNotFoundError(f"Job introuvable pour l'identifiant {job_id}.")
        
        location = self.job_repository.get_location_by_id(location_id)
        if not location:
            raise CountingValidationError(f"Emplacement introuvable pour l'identifiant {location_id}.")

        # Pour chaque comptage précédent requis, vérifier qu'il est terminé pour cet emplacement
        for order in required_orders:
            # Récupérer le comptage correspondant à cet ordre
            counting = self.counting_repository.get_by_inventory_and_order(job.inventory_id, order)
            if not counting:
                if target_order == 3:
                    raise CountingValidationError(
                        f"Impossible de lancer le 3ème comptage : le comptage d'ordre {order} n'existe pas pour l'inventaire."
                    )
                raise CountingValidationError(
                    f"Impossible de lancer le comptage d'ordre {target_order} : le comptage d'ordre {order} n'existe pas."
                )
            
            # Vérifier qu'il existe un JobDetail pour ce job, cet emplacement et ce comptage
            job_detail = self.job_repository.get_job_detail_by_job_location_and_counting(
                job, location, counting
            )

            if job_detail is None:
                assignment = self.assignment_repository.get_assignment_by_job_and_order(job.id, order)
                if assignment and assignment.status == 'TERMINE':
                    job_detail = self.job_repository.create_job_detail(
                        reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                        location=location,
                        job=job,
                        counting=counting,
                        status='TERMINE',
                        termine_date=timezone.now(),
                    )
                else:
                    if target_order == 3:
                        raise CountingValidationError(
                            f"Impossible de lancer le 3ème comptage pour cet emplacement : "
                            f"l'emplacement n'a pas de JobDetail pour le comptage d'ordre {order}."
                        )
                    raise CountingValidationError(
                        f"Impossible de lancer le comptage d'ordre {target_order} pour cet emplacement : "
                        f"l'emplacement n'a pas de JobDetail pour le comptage d'ordre {order}."
                    )
            
            # Vérifier que le JobDetail a le statut TERMINE
            if job_detail.status != 'TERMINE':
                if target_order == 3:
                    raise CountingValidationError(
                        f"Impossible de lancer le 3ème comptage pour cet emplacement : "
                        f"le comptage d'ordre {order} n'est pas terminé pour cet emplacement (statut actuel: {job_detail.status})."
                    )
                raise CountingValidationError(
                    f"Impossible de lancer le comptage d'ordre {target_order} pour cet emplacement : "
                    f"le comptage d'ordre {order} n'est pas terminé pour cet emplacement (statut actuel: {job_detail.status})."
                )

    def get_locations_with_discrepancy_for_job(self, job_id: int) -> List[int]:
        """
        Récupère la liste des IDs d'emplacements qui ont un écart (EcartComptage non résolu) pour un job donné.
        
        Args:
            job_id: Identifiant du job
            
        Returns:
            Liste des IDs d'emplacements avec écart
            
        Raises:
            CountingNotFoundError: Si le job n'existe pas
        """
        job = self.job_repository.get_job_by_id(job_id)
        if not job:
            raise CountingNotFoundError(f"Job introuvable pour l'identifiant {job_id}.")
        
        # Récupérer tous les JobDetail du job pour obtenir les locations
        job_details = JobDetail.objects.filter(job=job).select_related('location')
        location_ids = list(job_details.values_list('location_id', flat=True).distinct())
        
        if not location_ids:
            return []
        
        # Trouver les emplacements qui ont un EcartComptage non résolu
        # Un EcartComptage est lié à un inventory et a des ComptageSequence
        # qui sont liées à des CountingDetail qui ont des locations
        # Important : les CountingDetail doivent être liés au job spécifique
        from ..models import CountingDetail
        
        ecarts = EcartComptage.objects.filter(
            inventory=job.inventory,
            resolved=False
        )
        
        # Récupérer les CountingDetail liés au job qui ont des écarts
        counting_details_with_ecart = CountingDetail.objects.filter(
            job=job,
            location_id__in=location_ids,
            counting__inventory=job.inventory
        ).filter(
            counting_sequences__ecart_comptage__in=ecarts,
            counting_sequences__ecart_comptage__resolved=False
        ).values_list('location_id', flat=True).distinct()
        
        return list(counting_details_with_ecart)

    @transaction.atomic
    def launch_counting_for_jobs(self, job_ids: List[int], session_id: int) -> Dict[str, Any]:
        """
        Lance un comptage pour tous les emplacements avec écart des jobs fournis.
        
        Args:
            job_ids: Liste des identifiants des jobs
            session_id: Identifiant de la session (équipe mobile) à affecter
            
        Returns:
            Dict contenant les résultats du traitement pour chaque job et emplacement
            
        Raises:
            CountingValidationError: Données invalides ou incohérentes
            CountingNotFoundError: Ressource inexistante
            CountingCreationError: Erreur inattendue lors du traitement
        """
        if not job_ids:
            raise CountingValidationError("La liste des jobs ne peut pas être vide.")
        
        if session_id <= 0:
            raise CountingValidationError("L'identifiant de l'équipe doit être strictement positif.")
        
        session = UserApp.objects.filter(id=session_id, type='Mobile').first()
        if not session:
            raise CountingValidationError("La session fournie n'existe pas ou n'est pas de type 'Mobile'.")
        
        results = {
            'processed_jobs': [],
            'total_locations_found': 0,
            'total_locations_processed': 0,
            'total_locations_failed': 0,
            'errors': []
        }
        
        # Pour chaque job, trouver les emplacements avec écart et lancer le comptage
        for job_id in job_ids:
            try:
                # Récupérer les emplacements avec écart pour ce job
                location_ids = self.get_locations_with_discrepancy_for_job(job_id)
                
                if not location_ids:
                    results['processed_jobs'].append({
                        'job_id': job_id,
                        'locations_processed': 0,
                        'total_locations': 0,
                        'message': 'Aucun emplacement avec écart trouvé pour ce job'
                    })
                    continue
                
                results['total_locations_found'] += len(location_ids)
                
                # Pour chaque emplacement avec écart, lancer le comptage
                job_results = []
                for location_id in location_ids:
                    try:
                        result = self.launch_counting(job_id, location_id, session_id)
                        job_results.append({
                            'location_id': location_id,
                            'success': True,
                            'result': result
                        })
                        results['total_locations_processed'] += 1
                    except Exception as e:
                        job_results.append({
                            'location_id': location_id,
                            'success': False,
                            'error': str(e)
                        })
                        results['total_locations_failed'] += 1
                        results['errors'].append({
                            'job_id': job_id,
                            'location_id': location_id,
                            'error': str(e)
                        })
                
                results['processed_jobs'].append({
                    'job_id': job_id,
                    'locations_processed': len([r for r in job_results if r['success']]),
                    'total_locations': len(location_ids),
                    'details': job_results
                })
                
            except Exception as e:
                results['errors'].append({
                    'job_id': job_id,
                    'error': str(e)
                })
                results['processed_jobs'].append({
                    'job_id': job_id,
                    'locations_processed': 0,
                    'total_locations': 0,
                    'error': str(e)
                })
        
        return results

