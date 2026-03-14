"""
Use case pour standardiser les comptages des jobs dans le contexte des discrepancies.
"""
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class JobDiscrepancyStandardizationUseCase:
    """
    Use case pour standardiser les comptages des jobs.
    
    Ce use case garantit que tous les jobs ont le même nombre de comptages,
    en ajoutant des comptages vides si nécessaire.
    """
    
    def standardize_jobs_countings(
        self,
        jobs_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Standardise les comptages pour tous les jobs.
        
        Trouve le nombre maximum de comptages parmi tous les jobs,
        puis ajoute des comptages vides pour les jobs qui en ont moins.
        
        Args:
            jobs_data: Liste de dictionnaires contenant les données des jobs avec leurs assignments
            
        Returns:
            Liste de dictionnaires avec les comptages standardisés
        """
        if not jobs_data:
            return []
        
        # Trouver le nombre maximum de comptages parmi tous les jobs
        max_counting_order = 0
        for job_data in jobs_data:
            assignments = job_data.get('assignments', [])
            if assignments:
                max_order = max(
                    (a.get('counting_order') or 0 for a in assignments),
                    default=0
                )
                max_counting_order = max(max_counting_order, max_order)
        
        # Si aucun comptage trouvé, retourner les données telles quelles
        if max_counting_order == 0:
            return jobs_data
        
        # Standardiser chaque job
        standardized_jobs = []
        for job_data in jobs_data:
            standardized_job = self._standardize_single_job(
                job_data,
                max_counting_order
            )
            standardized_jobs.append(standardized_job)
        
        logger.debug(
            f"Standardisation terminée: {len(standardized_jobs)} jobs, "
            f"max_counting_order={max_counting_order}"
        )
        
        return standardized_jobs
    
    def _standardize_single_job(
        self,
        job_data: Dict[str, Any],
        max_counting_order: int
    ) -> Dict[str, Any]:
        """
        Standardise les comptages pour un seul job.
        
        Args:
            job_data: Dictionnaire contenant les données du job
            max_counting_order: Nombre maximum de comptages à avoir
            
        Returns:
            Dictionnaire avec les comptages standardisés
        """
        assignments = job_data.get('assignments', [])
        
        # Créer un dictionnaire des assignments par counting_order
        assignments_by_order = {
            a.get('counting_order'): a
            for a in assignments
            if a.get('counting_order') is not None
        }
        
        # Créer la liste standardisée des assignments
        standardized_assignments = []
        for order in range(1, max_counting_order + 1):
            if order in assignments_by_order:
                # Assignment existant
                standardized_assignments.append(assignments_by_order[order])
            else:
                # Assignment vide pour ce comptage
                standardized_assignments.append({
                    'status': None,
                    'counting_order': order,
                    'username': None,
                })
        
        # Créer une copie du job_data avec les assignments standardisés
        standardized_job = job_data.copy()
        standardized_job['assignments'] = standardized_assignments
        
        return standardized_job

