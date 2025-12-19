"""
Use case pour annuler des jobs avec leurs jobdetails et assignments
"""
from typing import List, Dict, Any
from ..services.job_service import JobService
from ..exceptions import JobCreationError
import logging

logger = logging.getLogger(__name__)

class JobCancelUseCase:
    """
    Use case pour annuler des jobs avec leurs jobdetails et assignments.
    
    Règles métier :
    - Seuls les jobs avec les statuts suivants peuvent être annulés : EN ATTENTE, VALIDE, AFFECTE, PRET
    - Si un job n'est pas dans un de ces statuts, il sera exclu avec un message d'erreur
    - Met le job au statut ANNULE avec annule_date
    - Met tous les JobDetails associés au statut ANNULE avec annule_date
    - Met tous les Assigments associés au statut ANNULE avec annule_date
    """
    
    def __init__(self):
        self.job_service = JobService()
    
    def execute(self, job_ids: List[int]) -> Dict[str, Any]:
        """
        Exécute la logique d'annulation des jobs
        
        Args:
            job_ids: Liste des IDs des jobs à annuler
            
        Returns:
            Dict[str, Any]: Résultat du traitement avec les statistiques
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        try:
            logger.info(f"Tentative d'annulation de {len(job_ids)} job(s)")
            result = self.job_service.cancel_jobs(job_ids)
            logger.info(
                f"Annulation réussie : {result['total_jobs_cancelled']} job(s), "
                f"{result['jobdetails_cancelled']} jobdetail(s) et "
                f"{result['assignments_cancelled']} assignment(s) annulé(s)"
            )
            return result
                
        except JobCreationError:
            raise
        except Exception as e:
            logger.error(
                f"Erreur inattendue lors de l'annulation des jobs {job_ids}: {str(e)}",
                exc_info=True
            )
            raise JobCreationError(
                f"Erreur inattendue lors de l'annulation des jobs {job_ids}: {str(e)}"
            )
