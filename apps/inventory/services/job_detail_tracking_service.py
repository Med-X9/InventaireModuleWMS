"""
Service pour le suivi des JobDetail avec leurs Assignment.
"""
from typing import List, Optional
import logging

from ..repositories.job_repository import JobRepository
from ..models import JobDetail, Assigment

logger = logging.getLogger(__name__)


class JobDetailTrackingService:
    """
    Service responsable de la récupération des JobDetail avec leurs Assignment.
    Gère la logique métier pour mapper JobDetail avec Assignment selon job et counting.
    """
    
    def __init__(self, job_repository: Optional[JobRepository] = None):
        """
        Initialise le service avec un repository.
        
        Args:
            job_repository: Repository pour l'accès aux données de job.
                          Si None, crée une nouvelle instance.
        """
        self.job_repository = job_repository or JobRepository()
    
    def get_job_details_with_assignments(
        self,
        inventory_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        counting_order: Optional[int] = None
    ) -> List[dict]:
        """
        Récupère les JobDetail avec leurs Assignment correspondants.
        
        Args:
            inventory_id: ID de l'inventaire (optionnel)
            warehouse_id: ID de l'entrepôt (optionnel)
            counting_order: Ordre du comptage (optionnel)
            
        Returns:
            Liste de dictionnaires contenant JobDetail avec Assignment mappé
        """
        # Récupérer les JobDetail depuis le repository
        job_details = self.job_repository.get_job_details_with_assignments(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id,
            counting_order=counting_order
        )
        
        # Mapper chaque JobDetail avec son Assignment correspondant
        result = []
        for job_detail in job_details:
            # Trouver l'Assignment correspondant selon job et counting
            assignment = self._find_assignment_for_job_detail(job_detail, counting_order)
            
            result.append({
                'job_detail': job_detail,
                'assignment': assignment
            })
        
        logger.debug(
            f"Récupéré {len(result)} JobDetail avec Assignment "
            f"(inventory_id={inventory_id}, warehouse_id={warehouse_id}, counting_order={counting_order})"
        )
        
        return result
    
    def _find_assignment_for_job_detail(
        self,
        job_detail: JobDetail,
        counting_order: Optional[int] = None
    ) -> Optional[Assigment]:
        """
        Trouve l'Assignment correspondant à un JobDetail selon job et counting.
        
        Args:
            job_detail: Le JobDetail à mapper
            counting_order: Ordre du comptage (optionnel)
            
        Returns:
            Assignment correspondant ou None
        """
        # Récupérer tous les assignments du job
        assignments = job_detail.job.assigment_set.all()
        
        # Si counting_order est spécifié, filtrer par ordre
        if counting_order:
            assignments = assignments.filter(counting__order=counting_order)
        
        # Si le JobDetail a un counting, filtrer par ce counting
        if job_detail.counting:
            assignments = assignments.filter(counting=job_detail.counting)
        
        # Retourner le premier assignment trouvé (ou None)
        return assignments.first()

