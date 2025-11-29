from typing import Optional, List, Set, Tuple
from django.utils import timezone
from django.db import transaction
from apps.inventory.models import Assigment, Job, JobDetail, Personne, EcartComptage, CountingDetail, Counting
from apps.users.models import UserApp
from apps.mobile.exceptions import (
    AssignmentNotFoundException,
    UserNotAssignedException,
    InvalidStatusTransitionException,
    JobNotFoundException,
    AssignmentAlreadyStartedException,
    PersonValidationException
    
)


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
            raise UserNotAssignedException(
                f"L'utilisateur {user_id} n'est pas affecté à l'assignment {assignment_id}"
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
                'nom': assignment.personne.nom,
                'prenom': assignment.personne.prenom
            } if assignment.personne else None,
            'personne_two': {
                'id': assignment.personne_two.id,
                'nom': assignment.personne_two.nom,
                'prenom': assignment.personne_two.prenom
            } if assignment.personne_two else None,
            'created_at': assignment.created_at,
            'updated_at': assignment.updated_at
        }
    
    @transaction.atomic
    def close_job(self, job_id: int, assignment_id: int, personnes_ids: Optional[List[int]] = None) -> dict:
        """
        Clôture un assignment et vérifie si le job peut être clôturé.
        
        Cette méthode :
        1. Marque l'assignment comme TERMINE
        2. Vérifie si TOUS les assignments du job sont TERMINE
        3. Vérifie si tous les EcartComptage de l'inventaire ont un final_result non null
        4. Si les deux conditions précédentes sont remplies, marque le job comme TERMINE
        
        Args:
            job_id: ID du job
            assignment_id: ID de l'assignment
            personnes_ids: Liste des IDs des personnes (min 1, max 2)
            
        Returns:
            Dictionnaire avec les informations du job et de l'assignment, incluant :
            - Le statut de clôture du job (job_closed)
            - Les informations sur les conditions de clôture (job_closure_status)
            
        Raises:
            JobNotFoundException: Si le job n'existe pas
            AssignmentNotFoundException: Si l'assignment n'existe pas
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
        
        # Vérifier que l'assignment existe
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
        assignment.save()
        
        # Synchroniser les CountingDetail entre les deux countings si nécessaire
        sync_result = self._synchronize_counting_details_if_needed(job, assignment)
        
        # Vérifier si tous les assignments du job sont terminés
        all_assignments = Assigment.objects.filter(job=job)
        all_assignments_terminated = all_assignments.exclude(status='TERMINE').count() == 0
        
        # Vérifier si tous les EcartComptage de l'inventaire ont un final_result non null
        # Si aucun EcartComptage n'existe, on considère que la condition est remplie
        ecart_comptages = EcartComptage.objects.filter(inventory=job.inventory)
        if ecart_comptages.exists():
            # Si des écarts existent, tous doivent avoir un final_result non null
            all_ecarts_have_final_result = ecart_comptages.filter(final_result__isnull=True).count() == 0
        else:
            # Si aucun écart n'existe, on considère que la condition est remplie
            all_ecarts_have_final_result = True
        
        # Si tous les assignments sont terminés ET tous les écarts ont un résultat final
        # alors on peut clôturer le job
        job_closed = False
        if all_assignments_terminated and all_ecarts_have_final_result:
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
                    'nom': p.nom,
                    'prenom': p.prenom,
                    'reference': p.reference
                } for p in personne_list
            ],
            'job_closure_status': {
                'all_assignments_terminated': all_assignments_terminated,
                'all_ecarts_have_final_result': all_ecarts_have_final_result,
                'job_closed': job_closed
            },
            'counting_detail_sync': sync_result
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
        
        return {
            'synchronized': True,
            'counting_order_1': counting_1.order,
            'counting_order_2': counting_2.order,
            'created_count': created_count,
            'missing_in_counting_1': len(missing_in_1),
            'missing_in_counting_2': len(missing_in_2)
        }
