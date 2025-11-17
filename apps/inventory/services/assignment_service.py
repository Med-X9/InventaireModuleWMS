"""
Service pour l'affectation des jobs de comptage.
"""
from typing import Dict, Any, List
from django.utils import timezone
from django.db import transaction
from ..interfaces.assignment_interface import IAssignmentService
from ..repositories.assignment_repository import AssignmentRepository
from ..exceptions.assignment_exceptions import (
    AssignmentValidationError, 
    AssignmentBusinessRuleError,
    AssignmentSessionError
)
from ..models import Job, Counting, Assigment
from apps.users.models import UserApp

class AssignmentService(IAssignmentService):
    """Service pour l'affectation des jobs de comptage."""
    
    def __init__(self, repository: AssignmentRepository = None):
        self.repository = repository or AssignmentRepository()

    def assign_jobs(self, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Affecte les jobs avec date_start et session
        
        Args:
            assignment_data: Données d'affectation contenant job_ids, counting_order, session_id, date_start
            
        Returns:
            Dict[str, Any]: Résultat de l'affectation
        """
        # Validation des données
        self.validate_assignment_data(assignment_data)
        
        job_ids = assignment_data['job_ids']
        counting_order = assignment_data['counting_order']
        session_id = assignment_data.get('session_id')
        date_start = assignment_data.get('date_start')
        
        with transaction.atomic():
            # Récupérer les jobs
            jobs = self.repository.get_jobs_by_ids(job_ids)
            
            # Vérifier que tous les jobs appartiennent au même inventaire
            inventory_ids = set(job.inventory_id for job in jobs)
            if len(inventory_ids) != 1:
                raise AssignmentValidationError("Tous les jobs doivent appartenir au même inventaire")
            
            inventory_id = list(inventory_ids)[0]
            
            # Vérifier que tous les jobs ont un statut autorisé pour l'affectation
            forbidden_statuses = ['EN ATTENTE']
            invalid_jobs = [job for job in jobs if job.status in forbidden_statuses]
            if invalid_jobs:
                invalid_jobs_info = [f"Job {job.reference} (statut: {job.status})" for job in invalid_jobs]
                raise AssignmentValidationError(
                    f"Les jobs en statut 'EN ATTENTE' ne peuvent pas être affectés. "
                    f"Ils doivent d'abord être validés. "
                    f"Jobs invalides : {', '.join(invalid_jobs_info)}"
                )
            
            # Récupérer le comptage
            counting = self.repository.get_counting_by_order_and_inventory(counting_order, inventory_id)
            if not counting:
                raise AssignmentValidationError(f"Comptage d'ordre {counting_order} non trouvé pour l'inventaire {inventory_id}")
            
            # Vérifier si on peut affecter une session à ce comptage
            if session_id and not self.can_assign_session_to_counting(counting_order, counting.count_mode):
                raise AssignmentSessionError(
                    f"Impossible d'affecter une session au comptage d'ordre {counting_order} "
                    f"avec le mode '{counting.count_mode}'. Les sessions ne sont autorisées que pour "
                    "les comptages 'en vrac' et 'par article' (pas pour 'image stock')."
                )
            
            # Vérifier que la session existe si fournie
            session = None
            if session_id:
                try:
                    session = UserApp.objects.get(id=session_id, type='Mobile')
                except UserApp.DoesNotExist:
                    raise AssignmentValidationError(f"Session avec l'ID {session_id} non trouvée ou n'est pas un mobile")
            
            # Créer ou mettre à jour les affectations
            assignments_created = 0
            assignments_updated = 0
            
            for job in jobs:
                # Recharger le job pour avoir le statut à jour
                job.refresh_from_db()
                
                # Vérifier s'il existe déjà une affectation pour ce job et ce comptage spécifique
                existing_assignment = self.repository.get_existing_assignment_for_job_and_counting(job.id, counting.id)
                
                if existing_assignment:
                    # Réaffectation : vérifier les statuts existants
                    current_job_status = job.status
                    current_assignment_status = existing_assignment.status
                    
                    # Statuts à préserver lors d'une réaffectation
                    preserved_statuses = ['PRET', 'TRANSFERT']
                    
                    # Déterminer le statut à utiliser pour l'affectation
                    # Si le job ou l'affectation a un statut à préserver, le conserver
                    if current_job_status in preserved_statuses or current_assignment_status in preserved_statuses:
                        # Conserver le statut existant (priorité au statut de l'affectation si présent)
                        new_assignment_status = current_assignment_status if current_assignment_status in preserved_statuses else current_job_status
                    else:
                        # Nouvelle affectation normale
                        new_assignment_status = 'AFFECTE'
                    
                    # Mettre à jour l'affectation existante pour ce comptage
                    existing_assignment.date_start = date_start or timezone.now()
                    existing_assignment.session = session
                    existing_assignment.status = new_assignment_status
                    
                    # Mettre à jour la date seulement si le statut change vers AFFECTE
                    if new_assignment_status == 'AFFECTE':
                        existing_assignment.affecte_date = timezone.now()
                    
                    existing_assignment.save()
                    assignments_updated += 1
                else:
                    # Créer une nouvelle affectation pour ce comptage
                    assignment_data = {
                        'job': job,
                        'counting': counting,
                        'date_start': date_start or timezone.now(),
                        'session': session,
                        'status': 'AFFECTE',
                        'affecte_date': timezone.now()
                    }
                    
                    assignment = self.repository.create_assignment(assignment_data)
                    assignments_created += 1
                
                # Vérifier si les deux comptages ont des sessions pour ce job
                should_update_status = self.should_update_job_status_to_affecte(job.id, inventory_id)
                
                # Recharger le job pour avoir le statut à jour après les modifications
                job.refresh_from_db()
                
                if should_update_status:
                    # Statuts à préserver pour le job lors d'une réaffectation
                    preserved_job_statuses = ['PRET', 'TRANSFERT']
                    
                    # Ne pas modifier le statut du job s'il est déjà PRET ou TRANSFERT
                    if job.status not in preserved_job_statuses:
                        # Mettre à jour le statut des affectations à AFFECTE (sauf celles préservées)
                        self.update_assignments_status_to_affecte(job.id, inventory_id)
                        
                        # Mettre à jour le statut du job à AFFECTE
                        self.repository.update_job_status(job.id, 'AFFECTE', 'affecte_date')
                else:
                    # Si le job est en attente, le mettre à VALIDE
                    if job.status == 'EN ATTENTE':
                        self.repository.update_job_status(job.id, 'VALIDE', 'valide_date')
            
            total_assignments = assignments_created + assignments_updated
            
            return {
                'success': True,
                'message': f"{assignments_created} affectations créées, {assignments_updated} affectations mises à jour",
                'assignments_created': assignments_created,
                'assignments_updated': assignments_updated,
                'total_assignments': total_assignments,
                'counting_order': counting_order,
                'inventory_id': inventory_id
            }

    def validate_assignment_data(self, assignment_data: Dict[str, Any]) -> None:
        """
        Valide les données d'affectation
        
        Args:
            assignment_data: Données d'affectation à valider
            
        Raises:
            AssignmentValidationError: Si les données sont invalides
        """
        errors = []
        
        # Validation des champs obligatoires
        if not assignment_data.get('job_ids'):
            errors.append("La liste des IDs des jobs est obligatoire")
        
        if not assignment_data.get('counting_order'):
            errors.append("L'ordre du comptage est obligatoire")
        
        # Validation des types
        job_ids = assignment_data.get('job_ids', [])
        if not isinstance(job_ids, list) or not job_ids:
            errors.append("job_ids doit être une liste non vide")
        
        counting_order = assignment_data.get('counting_order')
        if counting_order and not isinstance(counting_order, int):
            errors.append("counting_order doit être un entier")
        
        if counting_order and counting_order not in [1, 2]:
            errors.append("counting_order doit être 1 ou 2")
        
        # Validation de la date_start si fournie
        date_start = assignment_data.get('date_start')
        if date_start and not isinstance(date_start, (str, type(timezone.now()))):
            errors.append("date_start doit être une date valide")
        
        if errors:
            raise AssignmentValidationError(" | ".join(errors))

    def can_assign_session_to_counting(self, counting_order: int, count_mode: str) -> bool:
        """
        Vérifie si on peut affecter une session à un comptage
        
        Règles métier :
        - Pour le mode "image stock" : pas d'affectation de session (automatique)
        - Pour les modes "en vrac" et "par article" : affectation de session autorisée
        
        Args:
            counting_order: Ordre du comptage
            count_mode: Mode de comptage
            
        Returns:
            bool: True si l'affectation est autorisée
        """
        # Le mode "image stock" ne nécessite pas d'affectation de session
        if count_mode == "image stock":
            return False
        
        # Les modes "en vrac" et "par article" peuvent avoir une session
        if count_mode in ["en vrac", "par article"]:
            return True
        
        # Mode non reconnu
        return False

    def should_update_job_status_to_affecte(self, job_id: int, inventory_id: int) -> bool:
        """
        Vérifie si le statut du job doit être mis à AFFECTE
        
        Règle : Le statut devient AFFECTE si au moins un comptage a une session
        
        Args:
            job_id: ID du job
            inventory_id: ID de l'inventaire
            
        Returns:
            bool: True si le statut doit être mis à AFFECTE
        """
        # Récupérer les comptages de l'inventaire
        countings = Counting.objects.filter(inventory_id=inventory_id, order__in=[1, 2]).order_by('order')
        
        if countings.count() == 0:
            # S'il n'y a pas de comptages, ne pas mettre à jour le statut
            return False
        
        # Vérifier si le job a au moins une affectation avec session
        assignments_with_session = Assigment.objects.filter(
            job_id=job_id,
            counting__in=countings,
            session__isnull=False
        ).exists()
        
        # Le statut devient AFFECTE si au moins un comptage a une session
        return assignments_with_session

    def update_assignments_status_to_affecte(self, job_id: int, inventory_id: int) -> None:
        """
        Met à jour le statut des affectations à 'AFFECTE' pour un job donné
        Ne modifie pas les affectations avec des statuts à préserver (PRET, TRANSFERT)
        
        Args:
            job_id: ID du job
            inventory_id: ID de l'inventaire
        """
        # Récupérer toutes les affectations du job pour cet inventaire
        assignments = Assigment.objects.filter(
            job_id=job_id,
            counting__inventory_id=inventory_id
        )
        
        # Statuts à préserver lors de la mise à jour
        preserved_statuses = ['PRET', 'TRANSFERT']
        
        # Mettre à jour le statut et la date d'affectation
        current_time = timezone.now()
        for assignment in assignments:
            # Ne pas modifier les statuts à préserver
            if assignment.status not in preserved_statuses:
                assignment.status = 'AFFECTE'
                assignment.affecte_date = current_time
                assignment.save() 