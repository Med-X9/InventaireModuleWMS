from typing import Optional, List
from django.utils import timezone
from django.db import transaction
from apps.inventory.models import Assigment, Job, JobDetail, Personne
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
        Clôture un job en vérifiant que tous les emplacements sont terminés
        et en assignant les personnes à l'assignment.
        
        Args:
            job_id: ID du job
            assignment_id: ID de l'assignment
            personnes_ids: Liste des IDs des personnes (min 1, max 2)
            
        Returns:
            Dictionnaire avec les informations du job clôturé
            
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
        
        # Clôturer le job et l'assignment
        now = timezone.now()
        
        # Mettre à jour l'assignment
        assignment.status = 'TERMINE'
        assignment.save()
        
        
        return {
            'success': True,
            'message': f'Job {job.reference} et assignment {assignment.reference} clôturés avec succès',
            'job': {
                'id': job.id,
                'reference': job.reference,
                'status': job.status,
                'termine_date': job.termine_date,
                'total_emplacements': job_details.count()
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
            ]
        }
