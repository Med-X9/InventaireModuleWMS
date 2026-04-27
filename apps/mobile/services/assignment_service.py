from typing import Optional, List, Set, Tuple, Dict, Any
from django.utils import timezone
from django.db import transaction
from apps.inventory.models import Assigment, Job, JobDetail, Personne, EcartComptage, CountingDetail, Counting, ComptageSequence, Inventory
from apps.inventory.utils.ecart_consensus import calculate_ecart_consensus_result
from apps.users.models import UserApp
import logging
from apps.mobile.exceptions import (
    AssignmentNotFoundException,
    UserNotAssignedException,
    InvalidStatusTransitionException,
    JobNotFoundException,
    AssignmentAlreadyStartedException,
    PersonValidationException,
    AssignmentNotEntameException,
    AssignmentNotBloqueException,
    MaxEntameAssignmentsException
    
)

logger = logging.getLogger(__name__)


class AssignmentService:
    """
    Service pour la gestion des assignments et jobs
    """
    
    def __init__(self):
        self.allowed_status_transitions = {
            'EN ATTENTE': ['AFFECTE', 'PRET'],
            'AFFECTE': ['PRET', 'ENTAME'],
            'PRET': ['ENTAME', 'TRANSFERT'],
            'TRANSFERT': ['ENTAME', 'TERMINE'],
            'ENTAME': ['TERMINE'],
            'TERMINE': []
        }
    
    def verify_user_assignment(self, assignment_id: int, user_id: int) -> Assigment:
        """
        Vérifie que l'utilisateur est bien affecté à l'assignment
        
        Args:
            assignment_id: ID de l'assignment
            user_id: ID de l'utilisateur
            
        Returns:
            L'assignment si l'utilisateur est autorisé
            
        Raises:
            AssignmentNotFoundException: Si l'assignment n'existe pas
            UserNotAssignedException: Si l'utilisateur n'est pas affecté
        """
        try:
            assignment = Assigment.objects.get(id=assignment_id)
        except Assigment.DoesNotExist:
            raise AssignmentNotFoundException(f"Assignment avec l'ID {assignment_id} non trouvé")
        
        # Vérifier que l'utilisateur est affecté à cet assignment
        if assignment.session_id != user_id:
            # Récupérer le username de l'utilisateur pour le message d'erreur
            try:
                user = UserApp.objects.get(id=user_id)
                username = user.username
            except UserApp.DoesNotExist:
                username = f"ID {user_id}"
            
            raise UserNotAssignedException(
                f"L'utilisateur {username} n'est pas affecté à l'assignment {assignment_id}"
            )
        
        return assignment
    
    def verify_user_job(self, job_id: int, user_id: int) -> tuple[Job, Assigment]:
        """
        Vérifie que l'utilisateur est bien affecté au job et récupère l'assignment associé
        
        Args:
            job_id: ID du job
            user_id: ID de l'utilisateur
            
        Returns:
            Tuple (job, assignment) si l'utilisateur est autorisé
            
        Raises:
            JobNotFoundException: Si le job n'existe pas
            AssignmentNotFoundException: Si l'assignment associé n'existe pas
            UserNotAssignedException: Si l'utilisateur n'est pas affecté
        """
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise JobNotFoundException(f"Job avec l'ID {job_id} non trouvé")
        
        # Récupérer l'assignment associé à ce job
        try:
            assignment = Assigment.objects.get(job=job)
        except Assigment.DoesNotExist:
            raise AssignmentNotFoundException(f"Assignment non trouvé pour le job {job_id}")
        
        # Vérifier que l'utilisateur est affecté à cet assignment
        if assignment.session_id != user_id:
            raise UserNotAssignedException(
                f"L'utilisateur {user_id} n'est pas affecté au job {job_id}"
            )
        
        return job, assignment
    
    @transaction.atomic
    def update_assignment_and_job_status(self, assignment_id: int, user_id: int, 
                                      new_status: str) -> dict:
        """
        Met à jour simultanément le statut d'un assignment et de son job
        
        Args:
            assignment_id: ID de l'assignment
            user_id: ID de l'utilisateur
            new_status: Nouveau statut pour l'assignment et le job
            
        Returns:
            Dictionnaire avec les informations mises à jour
            
        Raises:
            AssignmentNotFoundException: Si l'assignment n'existe pas
            UserNotAssignedException: Si l'utilisateur n'est pas affecté à l'assignment
            InvalidStatusTransitionException: Si la transition de statut n'est pas autorisée
            JobNotFoundException: Si le job associé n'existe pas
            AssignmentAlreadyStartedException: Si l'assignment est déjà en statut ENTAME
            MaxEntameAssignmentsException: Si l'utilisateur a déjà 3 assignments ENTAME pour le même inventory
        """
        # Vérifier que l'utilisateur est autorisé
        assignment = self.verify_user_assignment(assignment_id, user_id)
        
        # Vérifier si l'assignment est déjà ENTAME et qu'on tente de le mettre à ENTAME
        current_assignment_status = assignment.status
        if current_assignment_status == 'ENTAME' and new_status == 'ENTAME':
            raise AssignmentAlreadyStartedException(
                f"L'assignment {assignment_id} est déjà entamé et ne peut pas être modifié"
            )
        
        # Vérifier la transition de statut pour l'assignment
        if new_status not in self.allowed_status_transitions.get(current_assignment_status, []):
            raise InvalidStatusTransitionException(
                f"Transition de statut non autorisée: {current_assignment_status} -> {new_status}"
            )
        
        # Récupérer le job associé
        job = assignment.job
        if not job:
            raise JobNotFoundException(f"Job non trouvé pour l'assignment {assignment_id}")
        
        # Vérifier la limite de 3 assignments ENTAME pour le même utilisateur et le même inventory
        # Cette vérification s'applique uniquement si on passe à ENTAME
        if new_status == 'ENTAME':
            # Récupérer l'inventory associé au job de l'assignment
            inventory = job.inventory
            
            # Compter les assignments ENTAME de l'utilisateur pour le même inventory
            # (exclure l'assignment actuel qui n'est pas encore en statut ENTAME)
            entame_count = Assigment.objects.filter(
                session_id=user_id,
                job__inventory=inventory,
                status='ENTAME'
            ).exclude(id=assignment_id).count()
            
            # Vérifier si l'utilisateur a déjà 3 assignments ENTAME
            if entame_count >= 3:
                raise MaxEntameAssignmentsException(
                    f"Vous ne pouvez pas lancer (entamer) cet assignment car vous avez déjà {entame_count} assignments "
                    f"en statut ENTAME pour le même inventaire. Maximum autorisé: 3."
                )
        
        # Mettre à jour le statut de l'assignment et la date correspondante
        assignment.status = new_status
        now = timezone.now()
        
        if new_status == 'ENTAME':
            assignment.entame_date = now
        elif new_status == 'PRET':
            assignment.pret_date = now
        elif new_status == 'TRANSFERT':
            assignment.transfert_date = now
        elif new_status == 'TERMINE':
            # Pour TERMINE, on peut aussi mettre à jour la date de fin
            pass
        
        assignment.save()
        
        # Mettre à jour le statut du job et la date correspondante
        job.status = new_status
        
        if new_status == 'ENTAME':
            job.entame_date = now
        elif new_status == 'PRET':
            job.pret_date = now
        elif new_status == 'TRANSFERT':
            job.transfert_date = now
        elif new_status == 'TERMINE':
            job.termine_date = now
        
        job.save()
        
        return {
            'assignment': {
                'id': assignment.id,
                'reference': assignment.reference,
                'status': assignment.status,
                'updated_at': assignment.updated_at
            },
            'job': {
                'id': job.id,
                'reference': job.reference,
                'status': job.status,
                'updated_at': job.updated_at
            },
            'message': f'Assignment et job mis à jour vers le statut {new_status}'
        }
    
    @transaction.atomic
    def update_assignment_and_job_status_by_job_id(self, job_id: int, user_id: int, 
                                                  new_status: str) -> dict:
        """
        Met à jour simultanément le statut d'un assignment et de son job en utilisant l'ID du job
        
        Args:
            job_id: ID du job
            user_id: ID de l'utilisateur
            new_status: Nouveau statut pour l'assignment et le job
            
        Returns:
            Dictionnaire avec les informations mises à jour
        """
        # Vérifier que l'utilisateur est autorisé et récupérer job et assignment
        job, assignment = self.verify_user_job(job_id, user_id)
        
        # Vérifier si l'assignment est déjà ENTAME et qu'on tente de le mettre à ENTAME
        current_assignment_status = assignment.status
        if current_assignment_status == 'ENTAME' and new_status == 'ENTAME':
            raise AssignmentAlreadyStartedException(
                f"L'assignment {assignment.id} est déjà entamé et ne peut pas être modifié"
            )
        
        # Vérifier la transition de statut pour l'assignment
        if new_status not in self.allowed_status_transitions.get(current_assignment_status, []):
            raise InvalidStatusTransitionException(
                f"Transition de statut non autorisée: {current_assignment_status} -> {new_status}"
            )
        
        # Vérifier la transition de statut pour le job
        current_job_status = job.status
        if new_status not in self.allowed_status_transitions.get(current_job_status, []):
            raise InvalidStatusTransitionException(
                f"Transition de statut du job non autorisée: {current_job_status} -> {new_status}"
            )
        
        # Mettre à jour le statut de l'assignment et la date correspondante
        assignment.status = new_status
        now = timezone.now()
        
        if new_status == 'ENTAME':
            assignment.entame_date = now
        elif new_status == 'PRET':
            assignment.pret_date = now
        elif new_status == 'TRANSFERT':
            assignment.transfert_date = now
        elif new_status == 'TERMINE':
            # Pour TERMINE, on peut aussi mettre à jour la date de fin
            pass
        
        assignment.save()
        
        # Mettre à jour le statut du job et la date correspondante
        job.status = new_status
        
        if new_status == 'ENTAME':
            job.entame_date = now
        elif new_status == 'PRET':
            job.pret_date = now
        elif new_status == 'TRANSFERT':
            job.transfert_date = now
        elif new_status == 'TERMINE':
            job.termine_date = now
        
        job.save()
        
        return {
            'assignment': {
                'id': assignment.id,
                'reference': assignment.reference,
                'status': assignment.status,
                'updated_at': assignment.updated_at
            },
            'job': {
                'id': job.id,
                'reference': job.reference,
                'status': job.status,
                'updated_at': job.updated_at
            },
            'message': f'Assignment et job mis à jour vers le statut {new_status}'
        }
    
    def get_assignment_details(self, assignment_id: int, user_id: int) -> dict:
        """
        Récupère les détails d'un assignment avec vérification des permissions
        
        Args:
            assignment_id: ID de l'assignment
            user_id: ID de l'utilisateur
            
        Returns:
            Dictionnaire avec les détails de l'assignment
        """
        assignment = self.verify_user_assignment(assignment_id, user_id)
        
        return {           
            'id': assignment.id,
            'reference': assignment.reference,
            'status': assignment.status,
            'job': {
                'id': assignment.job.id,
                'reference': assignment.job.reference,
                'status': assignment.job.status
            },
            'counting': {
                'id': assignment.counting.id,
                'reference': assignment.counting.reference
            },
            'personne': {
                'id': assignment.personne.id,
                'full_name': assignment.personne.full_name
            } if assignment.personne else None,
            'personne_two': {
                'id': assignment.personne_two.id,
                'full_name': assignment.personne_two.full_name
            } if assignment.personne_two else None,
            'created_at': assignment.created_at,
            'updated_at': assignment.updated_at
        }
    
    @transaction.atomic
    def close_job(self, job_id: int, assignment_id: int, personnes_ids: Optional[List[int]] = None, user_id: Optional[int] = None) -> dict:
        """
        Clôture un assignment et vérifie si le job peut être clôturé.

        Cette méthode :
        1. Marque l'assignment comme TERMINE
        2. Vérifie si TOUS les assignments du job sont TERMINE
        3. Vérifie si TOUS les écarts du job ont été résolus (final_result != null)
        4. Si tous les assignments sont terminés ET tous les écarts sont résolus, marque le job comme TERMINE

        Args:
            job_id: ID du job
            assignment_id: ID de l'assignment
            personnes_ids: Liste des IDs des personnes (min 1, max 2)
            user_id: ID de l'utilisateur authentifié (requis pour vérifier l'affectation)

        Returns:
            Dictionnaire avec les informations du job et de l'assignment, incluant :
            - Le statut de clôture du job (job_closed)
            - Les informations sur les conditions de clôture (job_closure_status)

        Raises:
            JobNotFoundException: Si le job n'existe pas
            AssignmentNotFoundException: Si l'assignment n'existe pas
            UserNotAssignedException: Si l'utilisateur n'est pas affecté à l'assignment
            InvalidStatusTransitionException: Si tous les emplacements ne sont pas terminés
            PersonValidationException: Si la validation des personnes échoue
        """
        # Valider les personnes
        if not personnes_ids:
            raise PersonValidationException(
                "Au moins une personne est requise pour fermer le job."
            )
        
        if len(personnes_ids) > 2:
            raise PersonValidationException(
                "Un maximum de deux personnes est autorisé pour fermer le job."
            )
        
        # Vérifier que les personnes existent
        personnes = Personne.objects.filter(id__in=personnes_ids)
        if personnes.count() != len(personnes_ids):
            found_ids = set(personnes.values_list('id', flat=True))
            missing_ids = set(personnes_ids) - found_ids
            raise PersonValidationException(
                f"Les personnes suivantes n'existent pas: {', '.join(map(str, missing_ids))}"
            )
        
        # Vérifier que le job existe
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise JobNotFoundException(f"Job avec l'ID {job_id} non trouvé")
        
        # Vérifier que l'utilisateur est affecté à l'assignment (si user_id est fourni)
        if user_id is not None:
            assignment = self.verify_user_assignment(assignment_id, user_id)
        else:
            # Si user_id n'est pas fourni, récupérer l'assignment sans vérification
            # (pour compatibilité avec les appels existants, mais déconseillé)
            try:
                assignment = Assigment.objects.get(id=assignment_id)
            except Assigment.DoesNotExist:
                raise AssignmentNotFoundException(f"Assignment avec l'ID {assignment_id} non trouvé")
        
        # Vérifier que l'assignment appartient au job
        if assignment.job_id != job_id:
            raise InvalidStatusTransitionException(
                f"L'assignment {assignment_id} n'appartient pas au job {job_id}"
            )
        
        # Récupérer tous les JobDetails du job
        job_details = JobDetail.objects.filter(job=job,counting=assignment.counting)
        
        # Vérifier que tous les emplacements sont terminés
        for job_detail in job_details:
            if job_detail.status != 'TERMINE':
                raise InvalidStatusTransitionException(
                    f"Le job ne peut pas être clôturé car certains emplacements ne sont pas terminés. "
                    f"Emplacement {job_detail.reference} (ID: {job_detail.id}) a le statut: {job_detail.status}"
                )
        
        # Si on arrive ici, tous les emplacements sont terminés
        # Assigner les personnes à l'assignment
        personne_list = list(personnes)
        assignment.personne = personne_list[0] if len(personne_list) > 0 else None
        assignment.personne_two = personne_list[1] if len(personne_list) > 1 else None
        
        # Clôturer l'assignment
        now = timezone.now()
        assignment.status = 'TERMINE'
        assignment.termine_date = now
        assignment.save()
        
        # Synchroniser les CountingDetail entre les deux countings si nécessaire
        sync_result = self._synchronize_counting_details_if_needed(job, assignment)

        # Déclencher la génération PDF asynchrone pour l'assignment terminé.
        # Le fichier sera stocké sous pdf_tasks/JOB-xxxx/comptage-xx.pdf
        try:
            from apps.inventory.views.pdf_views import enqueue_job_assignment_pdf_task

            job_reference = (job.reference or f"job-{job.id}").replace("\\", "-").replace("/", "-")
            counting_order = assignment.counting.order if assignment.counting and assignment.counting.order else 0
            output_subpath = f"{job_reference}/comptage-{int(counting_order):02d}.pdf"

            pdf_task = enqueue_job_assignment_pdf_task(
                job_id=job.id,
                assignment_id=assignment.id,
                equipe_id=None,
                output_subpath=output_subpath,
            )
            pdf_task_info = {
                "task_id": str(pdf_task.id),
                "status": pdf_task.status,
                "target_path": output_subpath,
            }
        except Exception as e:
            logger.error(
                f"Erreur lors du déclenchement async du PDF assignment={assignment.id}: {str(e)}",
                exc_info=True
            )
            pdf_task_info = {
                "task_id": None,
                "status": "ERROR",
                "target_path": None,
                "error": str(e),
            }
        
        # Vérifier si tous les assignments du job sont terminés
        all_assignments = Assigment.objects.filter(job=job)
        all_assignments_terminated = all_assignments.exclude(status='TERMINE').count() == 0

        # Vérifier si tous les écarts du job ont été résolus (final_result != null)
        all_ecarts_resolved = True
        if all_assignments_terminated:
            # Récupérer tous les EcartComptage liés au job via les ComptageSequence
            # EcartComptage est déjà importé au début du fichier
            unresolved_ecarts = EcartComptage.objects.filter(
                counting_sequences__counting_detail__job=job,
                final_result__isnull=True
            ).exists()

            if unresolved_ecarts:
                all_ecarts_resolved = False

        # Si tous les assignments sont terminés ET tous les écarts sont résolus, clôturer le job
        job_closed = False
        if all_assignments_terminated and all_ecarts_resolved:
            job.status = 'TERMINE'
            job.termine_date = now
            job.save()
            job_closed = True
        
        return {
            'success': True,
            'message': f'Assignment {assignment.reference} clôturé avec succès' + 
                      (f' et job {job.reference} clôturé' if job_closed else ''),
            'job': {
                'id': job.id,
                'reference': job.reference,
                'status': job.status,
                'termine_date': job.termine_date,
                'total_emplacements': job_details.count(),
                'closed': job_closed
            },
            'assignment': {
                'id': assignment.id,
                'reference': assignment.reference,
                'status': assignment.status
            },
            'personnes': [
                {
                    'id': p.id,
                    'full_name': p.full_name,
                    'reference': p.reference
                } for p in personne_list
            ],
            'job_closure_status': {
                'all_assignments_terminated': all_assignments_terminated,
                'all_ecarts_resolved': all_ecarts_resolved,
                'job_closed': job_closed
            },
            'counting_detail_sync': sync_result,
            'pdf_generation': pdf_task_info,
        }
    
    def _synchronize_counting_details_if_needed(
        self, 
        job: Job, 
        assignment: Assigment
    ) -> dict:
        """
        Synchronise les CountingDetail entre les deux countings (order 1 et 2) si nécessaire.
        
        Cette méthode :
        1. Vérifie le counting_order de l'assignment (1 ou 2)
        2. Si order = 1, vérifie si l'assignment order 2 est TERMINE
        3. Si order = 2, vérifie si l'assignment order 1 est TERMINE
        4. Si l'autre assignment est TERMINE, synchronise les CountingDetail :
           - Récupère tous les CountingDetail des deux countings pour ce job
           - Compare en batch et crée les lignes manquantes avec quantité 0
        
        Args:
            job: Le job concerné
            assignment: L'assignment qui vient d'être clôturé
            
        Returns:
            Dictionnaire avec les informations de synchronisation
        """
        counting_order = assignment.counting.order
        
        # Ne synchroniser que si counting_order est 1 ou 2
        if counting_order not in [1, 2]:
            return {
                'synchronized': False,
                'reason': f'Counting order {counting_order} ne nécessite pas de synchronisation'
            }
        
        # Déterminer l'autre counting_order
        other_counting_order = 2 if counting_order == 1 else 1
        
        # Récupérer l'assignment de l'autre counting pour ce job
        try:
            other_assignment = Assigment.objects.get(
                job=job,
                counting__order=other_counting_order
            )
        except Assigment.DoesNotExist:
            return {
                'synchronized': False,
                'reason': f'Assignment avec counting order {other_counting_order} non trouvé pour ce job'
            }
        
        # Vérifier si l'autre assignment est TERMINE
        if other_assignment.status != 'TERMINE':
            return {
                'synchronized': False,
                'reason': f'Assignment avec counting order {other_counting_order} n\'est pas encore TERMINE'
            }
        
        # Les deux assignments sont TERMINE, on peut synchroniser
        counting_1 = assignment.counting if counting_order == 1 else other_assignment.counting
        counting_2 = other_assignment.counting if counting_order == 1 else assignment.counting
        
        # Récupérer tous les CountingDetail des deux countings pour ce job
        counting_details_1 = CountingDetail.objects.filter(
            job=job,
            counting=counting_1
        ).select_related('location', 'product')
        
        counting_details_2 = CountingDetail.objects.filter(
            job=job,
            counting=counting_2
        ).select_related('location', 'product')
        
        # Créer des sets pour la comparaison rapide
        # Clé de comparaison : (location_id, product_id, dlc, n_lot)
        def get_comparison_key(cd: CountingDetail) -> Tuple[int, Optional[int], Optional[str], Optional[str]]:
            return (
                cd.location_id,
                cd.product_id if cd.product else None,
                cd.dlc.isoformat() if cd.dlc else None,
                cd.n_lot or None
            )
        
        # Créer des dictionnaires pour accès rapide
        details_1_dict = {get_comparison_key(cd): cd for cd in counting_details_1}
        details_2_dict = {get_comparison_key(cd): cd for cd in counting_details_2}
        
        # Trouver les lignes manquantes dans counting_2 (présentes dans counting_1 mais pas dans counting_2)
        missing_in_2 = []
        for key, cd_1 in details_1_dict.items():
            if key not in details_2_dict:
                missing_in_2.append({
                    'location': cd_1.location,
                    'product': cd_1.product,
                    'dlc': cd_1.dlc,
                    'n_lot': cd_1.n_lot,
                    'counting': counting_2,
                    'job': job
                })
        
        # Trouver les lignes manquantes dans counting_1 (présentes dans counting_2 mais pas dans counting_1)
        missing_in_1 = []
        for key, cd_2 in details_2_dict.items():
            if key not in details_1_dict:
                missing_in_1.append({
                    'location': cd_2.location,
                    'product': cd_2.product,
                    'dlc': cd_2.dlc,
                    'n_lot': cd_2.n_lot,
                    'counting': counting_1,
                    'job': job
                })
        
        # Créer les CountingDetail manquants avec quantité 0
        created_count = 0
        counting_details_to_create = []
        
        for item in missing_in_2:
            counting_detail = CountingDetail(
                quantity_inventoried=0,
                product=item['product'],
                dlc=item['dlc'],
                n_lot=item['n_lot'],
                location=item['location'],
                counting=item['counting'],
                job=item['job'],
                last_synced_at=timezone.now()
            )
            # Générer la référence temporaire
            counting_detail.reference = counting_detail.generate_reference(CountingDetail.REFERENCE_PREFIX)
            counting_details_to_create.append(counting_detail)
            created_count += 1
        
        for item in missing_in_1:
            counting_detail = CountingDetail(
                quantity_inventoried=0,
                product=item['product'],
                dlc=item['dlc'],
                n_lot=item['n_lot'],
                location=item['location'],
                counting=item['counting'],
                job=item['job'],
                last_synced_at=timezone.now()
            )
            # Générer la référence temporaire
            counting_detail.reference = counting_detail.generate_reference(CountingDetail.REFERENCE_PREFIX)
            counting_details_to_create.append(counting_detail)
            created_count += 1
        
        # Bulk create si nécessaire
        if counting_details_to_create:
            CountingDetail.objects.bulk_create(counting_details_to_create)
            
            # Régénérer les références avec les IDs réels
            for cd in counting_details_to_create:
                if cd.id:
                    cd.reference = cd.generate_reference(CountingDetail.REFERENCE_PREFIX)
            
            # Bulk update des références
            CountingDetail.objects.bulk_update(counting_details_to_create, fields=['reference'])
        
        # NOUVELLE ÉTAPE : Créer les ComptageSequence et mettre à jour les EcartComptage
        sequences_created = 0
        sequences_updated = 0
        ecarts_updated = 0
        
        # Récupérer tous les CountingDetail (existants + créés) pour les deux countings
        all_counting_details = list(counting_details_1) + list(counting_details_2) + counting_details_to_create
        
        # Grouper par (product, location, inventory) pour créer/gérer les EcartComptage
        ecarts_map = self._group_counting_details_by_ecart(all_counting_details, job.inventory)
        
        # Traiter chaque écart
        for ecart_key, ecart_data in ecarts_map.items():
            ecart = ecart_data['ecart']
            counting_details = ecart_data['counting_details']
            
            # Trier par counting.order pour avoir l'ordre chronologique
            counting_details.sort(key=lambda cd: cd.counting.order)
            
            # Récupérer toutes les séquences existantes pour cet écart (pour calculer ecart_with_previous)
            existing_sequences = list(
                ecart.counting_sequences.order_by('sequence_number')
            )
            existing_sequences_by_cd = {
                seq.counting_detail_id: seq for seq in existing_sequences
            }
            
            # Traiter chaque CountingDetail pour créer/mettre à jour les séquences
            sequences_to_create = []
            sequences_to_update = []
            current_sequence_number = ecart.total_sequences
            
            for idx, counting_detail in enumerate(counting_details):
                # Vérifier si une séquence existe déjà pour ce CountingDetail
                existing_sequence = existing_sequences_by_cd.get(counting_detail.id)
                
                if existing_sequence:
                    # MISE À JOUR : La séquence existe déjà
                    existing_sequence.quantity = counting_detail.quantity_inventoried
                    
                    # Recalculer ecart_with_previous
                    # Trouver la séquence précédente dans l'ordre chronologique (par sequence_number)
                    if existing_sequence.sequence_number > 1:
                        # Chercher la séquence avec sequence_number = existing_sequence.sequence_number - 1
                        previous_sequence = next(
                            (seq for seq in existing_sequences 
                             if seq.sequence_number == existing_sequence.sequence_number - 1),
                            None
                        )
                        
                        if previous_sequence:
                            existing_sequence.ecart_with_previous = abs(
                                counting_detail.quantity_inventoried - previous_sequence.quantity
                            )
                        else:
                            existing_sequence.ecart_with_previous = None
                    else:
                        existing_sequence.ecart_with_previous = None
                    
                    sequences_to_update.append(existing_sequence)
                else:
                    # CRÉATION : Nouvelle séquence
                    # Calculer le numéro de séquence
                    current_sequence_number += 1
                    sequence_number = current_sequence_number
                    
                    # Calculer ecart_with_previous
                    # Trouver la dernière séquence existante (par sequence_number)
                    ecart_value = None
                    if existing_sequences:
                        last_sequence = existing_sequences[-1]
                        ecart_value = abs(
                            counting_detail.quantity_inventoried - last_sequence.quantity
                        )
                    
                    # Créer la nouvelle séquence
                    new_sequence = ComptageSequence(
                        ecart_comptage=ecart,
                        sequence_number=sequence_number,
                        counting_detail=counting_detail,
                        quantity=counting_detail.quantity_inventoried,
                        ecart_with_previous=ecart_value
                    )
                    new_sequence.reference = new_sequence.generate_reference(ComptageSequence.REFERENCE_PREFIX)
                    sequences_to_create.append(new_sequence)
                    
                    # Ajouter à la liste des séquences existantes pour les prochains calculs
                    # (simulation en mémoire pour calculer les écarts suivants)
                    existing_sequences.append(new_sequence)
                    existing_sequences_by_cd[counting_detail.id] = new_sequence
            
            # Sauvegarder les séquences
            if sequences_to_create:
                ComptageSequence.objects.bulk_create(sequences_to_create)
                sequences_created += len(sequences_to_create)
            
            if sequences_to_update:
                ComptageSequence.objects.bulk_update(
                    sequences_to_update,
                    fields=['quantity', 'ecart_with_previous', 'updated_at']
                )
                sequences_updated += len(sequences_to_update)
            
            # Recalculer final_result et mettre à jour l'écart
            # Rafraîchir la requête pour inclure les nouvelles séquences créées
            ecart.refresh_from_db()
            all_sequences = list(ecart.counting_sequences.order_by('sequence_number'))
            
            if len(all_sequences) >= 2:
                final_result = calculate_ecart_consensus_result(
                    [s.quantity for s in all_sequences], ecart.final_result
                )
                ecart.final_result = final_result
            
            # Mettre à jour les métadonnées de l'écart
            ecart.total_sequences = len(all_sequences)
            ecart.stopped_sequence = all_sequences[-1].sequence_number if all_sequences else None
            ecart.save(update_fields=['total_sequences', 'stopped_sequence', 'final_result', 'updated_at'])
            ecarts_updated += 1
        
        return {
            'synchronized': True,
            'counting_order_1': counting_1.order,
            'counting_order_2': counting_2.order,
            'created_count': created_count,
            'missing_in_counting_1': len(missing_in_1),
            'missing_in_counting_2': len(missing_in_2),
            'sequences_created': sequences_created,
            'sequences_updated': sequences_updated,
            'ecarts_updated': ecarts_updated
        }
    
    def _group_counting_details_by_ecart(
        self, 
        counting_details: List[CountingDetail], 
        inventory: Inventory
    ) -> Dict[Tuple, Dict[str, Any]]:
        """
        Groupe les CountingDetail par (product, location, inventory) pour créer/gérer les EcartComptage.
        
        Un EcartComptage est identifié par un (product, location, inventory) unique.
        On cherche un EcartComptage existant qui a déjà une ComptageSequence liée à un CountingDetail
        avec le même (product, location, inventory).
        
        Args:
            counting_details: Liste de tous les CountingDetail à traiter
            inventory: L'inventaire associé
            
        Returns:
            Dictionnaire avec clé (product_id, location_id, inventory_id) et valeur {
                'ecart': EcartComptage,
                'counting_details': List[CountingDetail]
            }
        """
        ecarts_map = {}
        
        for counting_detail in counting_details:
            # Vérifier que product et location existent (obligatoires pour EcartComptage)
            if not counting_detail.product or not counting_detail.location:
                logger.warning(
                    f"CountingDetail {counting_detail.id} ignoré : product ou location manquant"
                )
                continue
            
            key = (
                counting_detail.product.id,
                counting_detail.location.id,
                inventory.id
            )
            
            if key not in ecarts_map:
                # Chercher un EcartComptage existant pour ce (product, location, inventory)
                # via les ComptageSequence existantes
                existing_ecart = None
                existing_sequence = ComptageSequence.objects.filter(
                    counting_detail__product_id=counting_detail.product.id,
                    counting_detail__location_id=counting_detail.location.id,
                    counting_detail__job__inventory=inventory,
                    ecart_comptage__inventory=inventory
                ).select_related('ecart_comptage').first()
                
                if existing_sequence:
                    existing_ecart = existing_sequence.ecart_comptage
                    logger.info(
                        f"EcartComptage existant trouvé : {existing_ecart.reference} "
                        f"pour (product={counting_detail.product.id}, location={counting_detail.location.id})"
                    )
                else:
                    # Créer un nouvel EcartComptage
                    existing_ecart = EcartComptage(
                        inventory=inventory,
                        total_sequences=0,
                        resolved=False,
                        stopped_reason=None,
                        final_result=None,
                        justification=None
                    )
                    existing_ecart.reference = existing_ecart.generate_reference(EcartComptage.REFERENCE_PREFIX)
                    existing_ecart.save()
                    logger.info(f"Nouvel EcartComptage créé : {existing_ecart.reference}")
                
                ecarts_map[key] = {
                    'ecart': existing_ecart,
                    'counting_details': []
                }
            
            ecarts_map[key]['counting_details'].append(counting_detail)
        
        return ecarts_map
    
    @transaction.atomic
    def block_assignment(self, assignment_id: int, user_id: int) -> dict:
        """
        Bloque un assignment en changeant son statut vers ANNULE.
        Cette opération n'est autorisée que si l'assignment est en statut ENTAME.
        
        Args:
            assignment_id: ID de l'assignment à bloquer
            user_id: ID de l'utilisateur
            
        Returns:
            Dictionnaire avec les informations de l'assignment bloqué
            
        Raises:
            AssignmentNotFoundException: Si l'assignment n'existe pas
            UserNotAssignedException: Si l'utilisateur n'est pas affecté à l'assignment
            AssignmentNotEntameException: Si l'assignment n'est pas en statut ENTAME
        """
        # Vérifier que l'utilisateur est autorisé
        assignment = self.verify_user_assignment(assignment_id, user_id)
        
        # Vérifier que l'assignment est en statut ENTAME
        if assignment.status != 'ENTAME':
            raise AssignmentNotEntameException(
                f"L'assignment {assignment_id} ne peut pas être bloqué car son statut est '{assignment.status}'. "
                f"Seuls les assignments en statut 'ENTAME' peuvent être bloqués."
            )
        
        # Mettre à jour le statut vers bloqué
        now = timezone.now()
        assignment.status = 'BLOQUE'
        assignment.bloqued_date = now
        assignment.save(update_fields=['status', 'bloqued_date', 'updated_at'])
        
        # Récupérer le job associé pour information
        job = assignment.job
        
        return {
            'assignment': {
                'id': assignment.id,
                'reference': assignment.reference,
                'status': assignment.status,
                'previous_status': 'ENTAME',
                'bloqued_date': assignment.bloqued_date,
                'updated_at': assignment.updated_at
            },
            'job': {
                'id': job.id,
                'reference': job.reference,
                'status': job.status
            } if job else None,
            'message': f'Assignment {assignment.reference} bloqué avec succès'
        }
    
    @transaction.atomic
    def unblock_assignment(self, assignment_id: int, user_id: int) -> dict:
        """
        Débloque un assignment en changeant son statut vers ENTAME.
        Cette opération n'est autorisée que si l'assignment est en statut bloqué.
        Vérifie également qu'il n'y a pas déjà 3 assignments ENTAME pour le même utilisateur et inventory.
        
        Args:
            assignment_id: ID de l'assignment à débloquer
            user_id: ID de l'utilisateur
            
        Returns:
            Dictionnaire avec les informations de l'assignment débloqué
            
        Raises:
            AssignmentNotFoundException: Si l'assignment n'existe pas
            UserNotAssignedException: Si l'utilisateur n'est pas affecté à l'assignment
            AssignmentNotBloqueException: Si l'assignment n'est pas en statut bloqué
            MaxEntameAssignmentsException: Si l'utilisateur a déjà 3 assignments ENTAME pour le même inventory
        """
        # Vérifier que l'utilisateur est autorisé
        assignment = self.verify_user_assignment(assignment_id, user_id)
        
        # Vérifier que l'assignment est en statut bloqué
        if assignment.status != 'BLOQUE':
            raise AssignmentNotBloqueException(
                f"L'assignment {assignment_id} ne peut pas être débloqué car son statut est '{assignment.status}'. "
                f"Seuls les assignments en statut 'BLOQUE' peuvent être débloqués."
            )
        
        # Récupérer l'inventory associé au job de l'assignment
        inventory = assignment.job.inventory
        
        # Compter les assignments ENTAME de l'utilisateur pour le même inventory
        # (exclure l'assignment actuel qui est encore en statut bloqué)
        entame_count = Assigment.objects.filter(
            session_id=user_id,
            job__inventory=inventory,
            status='ENTAME'
        ).exclude(id=assignment_id).count()
        
        # Vérifier si l'utilisateur a déjà 3 assignments ENTAME
        if entame_count >= 3:
            raise MaxEntameAssignmentsException(
                f"Vous ne pouvez pas débloquer cet assignment car vous avez déjà {entame_count} assignments en statut ENTAME "
                f"pour le même inventaire. Pour débloquer, vous devez terminer ou bloquer un assignment."
            )
        
        # Mettre à jour le statut vers ENTAME
        now = timezone.now()
        assignment.status = 'ENTAME'
        assignment.debloqued_date = now
        assignment.save(update_fields=['status', 'debloqued_date', 'updated_at'])
        
        # Récupérer le job associé pour information
        job = assignment.job
        
        return {
            'assignment': {
                'id': assignment.id,
                'reference': assignment.reference,
                'status': assignment.status,
                'previous_status': 'BLOQUE',
                'debloqued_date': assignment.debloqued_date,
                'updated_at': assignment.updated_at
            },
            'job': {
                'id': job.id,
                'reference': job.reference,
                'status': job.status
            } if job else None,
            'message': f'Assignment {assignment.reference} débloqué avec succès'
        }