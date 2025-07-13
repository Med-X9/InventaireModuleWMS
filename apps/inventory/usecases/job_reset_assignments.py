"""
Use case pour la remise en attente des jobs selon leur statut actuel
"""
from typing import List, Dict, Any
from django.db import transaction
from django.utils import timezone
from ..models import Job, Assigment, JobDetailRessource
from ..exceptions import JobCreationError
import logging

logger = logging.getLogger(__name__)

class JobResetAssignmentsUseCase:
    """
    Use case pour remettre les jobs en attente selon leur statut actuel
    """
    
    def __init__(self):
        pass
    
    def execute(self, job_ids: List[int]) -> Dict[str, Any]:
        """
        Exécute la logique de reset des assignments selon le statut du job
        
        Args:
            job_ids: Liste des IDs des jobs à traiter
            
        Returns:
            Dict[str, Any]: Résultat du traitement
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        try:
            with transaction.atomic():
                # Vérifier que tous les jobs existent
                jobs = Job.objects.filter(id__in=job_ids)
                found_job_ids = set(job.id for job in jobs)
                requested_job_ids = set(job_ids)
                
                # Identifier les jobs qui n'existent pas
                missing_job_ids = requested_job_ids - found_job_ids
                if missing_job_ids:
                    missing_jobs_str = ', '.join(map(str, sorted(missing_job_ids)))
                    raise JobCreationError(f"Jobs non trouvés avec les IDs : {missing_jobs_str}")
                
                # Traiter chaque job selon son statut
                jobs_processed = 0
                assignments_reset = 0
                ressources_deleted = 0
                
                for job in jobs:
                    logger.info(f"Traitement du job {job.reference} (statut actuel: {job.status})")
                    
                    if job.status == 'VALIDE':
                        # Si le job est VALIDE : le remettre en attente et supprimer la date de validation
                        self._reset_valid_job(job)
                        jobs_processed += 1
                        
                    elif job.status in ['AFFECTE', 'PRET']:
                        # Si le job est AFFECTE ou PRET : remettre les assignments en attente et mettre le job en attente
                        assignments_count, ressources_count = self._reset_assigned_job(job)
                        assignments_reset += assignments_count
                        ressources_deleted += ressources_count
                        jobs_processed += 1
                        
                    else:
                        # Pour les autres statuts, juste logger
                        logger.info(f"Job {job.reference} avec statut {job.status} - aucun traitement nécessaire")
                
                return {
                    'success': True,
                    'jobs_processed': jobs_processed,
                    'assignments_reset': assignments_reset,
                    'ressources_deleted': ressources_deleted,
                    'message': f'Jobs traités avec succès: {jobs_processed} jobs, {assignments_reset} assignments reset, {ressources_deleted} ressources supprimées'
                }
                
        except JobCreationError:
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors du reset des assignments: {str(e)}", exc_info=True)
            raise JobCreationError(f"Erreur inattendue lors du reset des assignments: {str(e)}")
    
    def _reset_valid_job(self, job: Job) -> None:
        """
        Remet un job VALIDE en attente
        
        Args:
            job: Le job à traiter
        """
        logger.info(f"Reset du job VALIDE {job.reference}")
        
        # Remettre le job en attente
        job.status = 'EN ATTENTE'
        
        # Supprimer toutes les dates et ajouter en_attente_date
        job.valide_date = None
        job.pret_date = None
        job.affecte_date = None
        job.en_attente_date = timezone.now()
        job.save()
        
        logger.info(f"Job {job.reference} remis en attente avec succès")
    
    def _reset_assigned_job(self, job: Job) -> tuple[int, int]:
        """
        Remet un job AFFECTE ou PRET en attente
        
        Args:
            job: Le job à traiter
            
        Returns:
            tuple[int, int]: (nombre d'assignments reset, nombre de ressources supprimées)
        """
        logger.info(f"Reset du job {job.status} {job.reference}")
        
        # Remettre le job en attente
        job.status = 'EN ATTENTE'
        
        # Supprimer toutes les dates et ajouter en_attente_date
        job.valide_date = None
        job.pret_date = None
        job.affecte_date = None
        job.en_attente_date = timezone.now()
        job.save()
        
        # Récupérer tous les assignements du job
        assignments = Assigment.objects.filter(job=job)
        assignments_count = 0
        
        # Remettre tous les assignements en attente
        for assignment in assignments:
            assignment.session = None
            assignment.status = 'EN ATTENTE'
            # Vider toutes les dates
            assignment.affecte_date = None
            assignment.pret_date = None
            assignment.transfert_date = None
            assignment.entame_date = None
            assignment.save()
            assignments_count += 1
        
        # Supprimer tous les JobDetailRessource du job
        ressources_deleted = JobDetailRessource.objects.filter(job=job).delete()[0]
        
        logger.info(f"Job {job.reference}: {assignments_count} assignments reset, {ressources_deleted} ressources supprimées")
        
        return assignments_count, ressources_deleted 