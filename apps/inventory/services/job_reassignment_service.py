import logging
from django.db import transaction
from django.utils import timezone
from ..models import Job, JobDetail, Assigment, CountingDetail, NSerieInventory, EcartComptage, ComptageSequence, Counting
from ..repositories.job_repository import JobRepository
from ..repositories.assignment_repository import AssignmentRepository
from typing import Dict, Any
from django.core.exceptions import ObjectDoesNotExist, ValidationError

logger = logging.getLogger(__name__)

class JobReassignmentService:
    """
    Service pour la réaffectation d'équipes à des jobs avec gestion des statuts et nettoyage des données
    """

    def __init__(self):
        self.job_repository = JobRepository()
        self.assignment_repository = AssignmentRepository()

    @transaction.atomic
    def reassign_team_to_job_counting(self, job_id: int, team_id: int, counting_order: int, complete: bool = False) -> Dict[str, Any]:
        """
        Réaffecte une équipe à un job pour un comptage spécifique

        Args:
            job_id: ID du job
            team_id: ID de l'équipe (session)
            counting_order: Ordre du comptage (1 ou 2)
            complete: Si True, supprime uniquement les données du comptage spécifié (pas les autres comptages)

        Returns:
            Dict avec les informations sur l'opération effectuée

        Raises:
            ValidationError: Si les validations échouent
            ObjectDoesNotExist: Si les objets n'existent pas
        """
        try:
            # 1. Récupérer et valider les objets
            job = self._get_job_by_id(job_id)
            session = self._get_session_by_id(team_id)
            counting = self._get_counting_by_job_and_order(job, counting_order)

            # 2. Vérifier les règles de validation
            self._validate_reassignment_rules(job, counting, session)

            # 3. Si complete=True, nettoyer toutes les données
            if complete:
                self._clean_job_counting_data(job, counting)

            # 4. Réaffecter l'équipe
            assignment = self._reassign_team_to_counting(job, counting, session)

            # 5. Mettre à jour les statuts
            self._update_statuses_after_reassignment(job, counting)

            # 6. Calculer et mettre à jour le statut du job
            self._update_job_status_based_on_assignments(job)

            return {
                'success': True,
                'message': f'Équipe {session} réaffectée au job {job.reference} pour le comptage {counting_order}',
                'job_id': job.id,
                'job_reference': job.reference,
                'assignment_id': assignment.id,
                'counting_order': counting_order,
                'complete_cleaned': complete
            }

        except Exception as e:
            logger.error(f"Erreur lors de la réaffectation: {str(e)}")
            raise

    def _get_job_by_id(self, job_id: int) -> Job:
        """Récupère un job par son ID"""
        try:
            job = Job.objects.get(id=job_id)
            return job
        except Job.DoesNotExist:
            raise ValidationError(f"Job avec l'ID {job_id} n'existe pas")

    def _get_session_by_id(self, session_id: int):
        """Récupère une session par son ID"""
        try:
            from apps.users.models import UserApp
            session = UserApp.objects.get(id=session_id, type='Mobile')
            return session
        except Exception as e:
            raise ValidationError(f"Session (équipe) avec l'ID {session_id} n'existe pas ou n'est pas de type Mobile: {str(e)}")

    def _get_counting_by_job_and_order(self, job: Job, counting_order: int) -> Counting:
        """Récupère le comptage selon l'ordre pour le job"""
        countings = Counting.objects.filter(inventory=job.inventory).order_by('created_at')

        if counting_order == 1:
            counting = countings.first()
        elif counting_order == 2:
            counting = countings[1] if countings.count() > 1 else None
        else:
            counting = None

        if not counting:
            raise ValidationError(f"Comptage {counting_order} non trouvé pour l'inventaire {job.inventory.reference}")

        return counting

    def _validate_reassignment_rules(self, job: Job, counting: Counting, session):
        """
        Valide les règles de réaffectation :
        - L'assignement existant ne doit pas être en statut TERMINE
        """
        # Chercher l'assignement existant pour ce job et ce comptage
        existing_assignment = Assigment.objects.filter(
            job=job,
            counting=counting
        ).first()

        if existing_assignment and existing_assignment.status == 'TERMINE':
            raise ValidationError(
                f"Impossible de réaffecter l'équipe : l'assignement pour le job {job.reference} "
                f"et le comptage {counting.reference} est déjà terminé"
            )

    def _clean_job_counting_data(self, job: Job, counting: Counting):
        """
        Nettoie toutes les données liées au job et au comptage spécifique :
        - CountingDetail (du comptage spécifique uniquement)
        - NSerieInventory (liés aux CountingDetail du comptage)
        - ComptageSequence (liés aux CountingDetail du comptage)
        - EcartComptage (uniquement ceux qui n'ont plus de ComptageSequence après suppression)
        - Met à jour les statuts JobDetail et Assigment
        """
        logger.info(f"Nettoyage complet des données pour job {job.id} et counting {counting.id}")

        # 1. Récupérer les CountingDetail du comptage spécifique uniquement
        counting_details = CountingDetail.objects.filter(job=job, counting=counting)
        
        if not counting_details.exists():
            logger.info(f"Aucun CountingDetail trouvé pour job {job.id} et counting {counting.id}")
            return

        # 2. Récupérer les ComptageSequence liés à ces CountingDetail
        comptage_sequences = ComptageSequence.objects.filter(
            counting_detail__in=counting_details
        )
        
        # 3. Récupérer les EcartComptage liés à ces ComptageSequence (avant suppression)
        ecart_comptages_ids = comptage_sequences.values_list('ecart_comptage_id', flat=True).distinct()
        ecart_comptages = EcartComptage.objects.filter(id__in=ecart_comptages_ids)

        # 4. Supprimer NSerieInventory liés aux CountingDetail du comptage
        NSerieInventory.objects.filter(counting_detail__in=counting_details).delete()

        # 5. Supprimer ComptageSequence liés aux CountingDetail du comptage
        comptage_sequences.delete()

        # 6. Supprimer les EcartComptage qui n'ont plus de ComptageSequence
        # (uniquement ceux qui étaient liés au comptage qu'on nettoie)
        for ecart in ecart_comptages:
            remaining_sequences = ComptageSequence.objects.filter(ecart_comptage=ecart).exists()
            if not remaining_sequences:
                ecart.delete()

        # 7. Supprimer CountingDetail du comptage
        counting_details.delete()

        # 8. Remettre les JobDetail à "EN ATTENTE"
        # Note: On remet tous les JobDetail du job à "EN ATTENTE" car le nettoyage
        # d'un comptage peut affecter l'état global du job
        JobDetail.objects.filter(job=job).update(
            status='EN ATTENTE',
            en_attente_date=timezone.now()
        )

        # 9. L'assignement sera mis à jour dans _reassign_team_to_counting selon le cas

    def _reassign_team_to_counting(self, job: Job, counting: Counting, session) -> Assigment:
        """
        Réaffecte l'équipe au comptage du job
        Crée ou met à jour l'assignement
        """
        assignment, created = Assigment.objects.get_or_create(
            job=job,
            counting=counting,
            defaults={
                'status': 'AFFECTE',
                'session': session,
                'affecte_date': timezone.now()
            }
        )

        if not created:
            # Mettre à jour l'assignement existant (réaffectation)
            assignment.session = session
            assignment.status = 'TRANSFERT'  # Changement d'équipe = transfert
            assignment.transfert_date = timezone.now()
            assignment.save()

        return assignment

    def _update_statuses_after_reassignment(self, job: Job, counting: Counting):
        """
        Met à jour les statuts après réaffectation
        Note: Le statut de l'assignement est déjà correctement défini dans _reassign_team_to_counting
        - 'AFFECTE' pour nouvelle affectation
        - 'TRANSFERT' pour réaffectation
        Ici on ne fait que mettre à jour la date
        """
        # Mettre à jour seulement la date d'affectation, pas le statut
        # Le statut est déjà correctement défini dans _reassign_team_to_counting
        assignment = Assigment.objects.get(job=job, counting=counting)
        if assignment.status == 'AFFECTE':
            assignment.affecte_date = timezone.now()
        elif assignment.status == 'TRANSFERT':
            assignment.transfert_date = timezone.now()
        assignment.save()

    def _update_job_status_based_on_assignments(self, job: Job):
        """
        Met à jour le statut du job selon les assignments des comptages 1 et 2 :
        - Si au moins un assignment est ENTAME -> job = ENTAME (priorité haute)
        - Si au moins un assignment est TRANSFERT -> job = TRANSFERT (priorité basse)
        - Si les deux assignments sont TRANSFERT -> job = TRANSFERT
        """
        # Récupérer les assignments des comptages 1 et 2
        assignments = Assigment.objects.filter(job=job)

        # Compter les statuts
        transfert_count = assignments.filter(status='TRANSFERT').count()
        entame_count = assignments.filter(status='ENTAME').count()

        new_status = None

        # Priorité : ENTAME > TRANSFERT
        if entame_count >= 1:
            new_status = 'ENTAME'
        elif transfert_count >= 1:
            new_status = 'TRANSFERT'

        if new_status:
            job.status = new_status
            if new_status == 'TRANSFERT':
                job.transfert_date = timezone.now()
            elif new_status == 'ENTAME':
                job.entame_date = timezone.now()
            job.save()
