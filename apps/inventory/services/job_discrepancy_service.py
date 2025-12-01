"""
Service pour calculer les écarts entre le 1er et le 2ème comptage d'un job.
"""
from typing import Dict, Any, List, Optional
from ..repositories.job_repository import JobRepository
from ..models import Job, Assigment, CountingDetail
import logging

logger = logging.getLogger(__name__)


class JobDiscrepancyService:
    """
    Service pour calculer les écarts entre le 1er et le 2ème comptage.
    Contient la logique métier pour le calcul des écarts.
    """
    
    def __init__(self, job_repository: Optional[JobRepository] = None):
        """
        Initialise le service avec un repository.
        
        Args:
            job_repository: Repository pour l'accès aux données (injection de dépendance)
        """
        self.job_repository = job_repository or JobRepository()
    
    def get_jobs_with_discrepancies(
        self,
        inventory_id: int,
        warehouse_id: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère les jobs avec leurs assignments et calcule les écarts entre le 1er et 2ème comptage.
        
        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt
            
        Returns:
            Liste de dictionnaires contenant les informations des jobs avec écarts calculés
            
        Raises:
            ValueError: Si l'inventaire ou le warehouse n'existe pas
        """
        # Vérifier que l'inventaire existe
        inventory = self.job_repository.get_inventory_by_id(inventory_id)
        if not inventory:
            raise ValueError(f"Inventaire avec l'ID {inventory_id} non trouvé")
        
        # Vérifier que le warehouse existe
        warehouse = self.job_repository.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            raise ValueError(f"Warehouse avec l'ID {warehouse_id} non trouvé")
        
        # Récupérer les jobs avec leurs assignments et counting details
        jobs = self.job_repository.get_jobs_with_assignments_and_counting_details(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id
        )
        
        result = []
        for job in jobs:
            # Récupérer les assignments du job
            assignments = self.job_repository.get_assignments_by_job(job)
            
            # Filtrer seulement les assignments avec counting_order 1 et 2
            assignments_filtered = [
                assignment for assignment in assignments
                if assignment.counting and assignment.counting.order in [1, 2]
            ]
            
            # Calculer les écarts entre le 1er et 2ème comptage
            discrepancy_info = self._calculate_discrepancies(job)
            
            # Formater les assignments (seulement counting_order, status, counting_reference, session_full_name)
            assignments_data = [
                {
                    'status': assignment.status,
                    'counting_reference': assignment.counting.reference if assignment.counting else None,
                    'counting_order': assignment.counting.order if assignment.counting else None,
                    'session_full_name': f"{assignment.session.prenom} {assignment.session.nom}" if assignment.session else None,
                }
                for assignment in assignments_filtered
            ]
            
            result.append({
                'job_id': job.id,
                'job_reference': job.reference,
                'job_status': job.status,
                'assignments': assignments_data,
                'discrepancy_count': discrepancy_info['discrepancy_count'],
                'discrepancy_rate': discrepancy_info['discrepancy_rate'],
                'total_lines_counting_1': discrepancy_info['total_lines_counting_1'],
                'total_lines_counting_2': discrepancy_info['total_lines_counting_2'],
                'common_lines_count': discrepancy_info['common_lines_count'],
            })
        
        return result
    
    def _calculate_discrepancies(self, job: Job) -> Dict[str, Any]:
        """
        Calcule les écarts entre le 1er et le 2ème comptage pour un job.
        
        Args:
            job: Job avec les counting details préchargés
            
        Returns:
            Dictionnaire contenant:
            - discrepancy_count: Nombre de lignes avec écart (lignes communes avec quantités différentes)
            - discrepancy_rate: Taux d'écart (en pourcentage) basé sur les lignes communes aux deux comptages
            - total_lines_counting_1: Nombre total de lignes du 1er comptage
            - total_lines_counting_2: Nombre total de lignes du 2ème comptage
            - common_lines_count: Nombre de lignes communes aux deux comptages
        """
        # Récupérer les counting details depuis les attributs temporaires
        counting_details_1 = getattr(job, '_counting_details_1', {})
        counting_details_2 = getattr(job, '_counting_details_2', {})
        
        total_lines_counting_1 = len(counting_details_1)
        total_lines_counting_2 = len(counting_details_2)
        
        # Créer un ensemble des clés communes aux deux comptages (intersection)
        # On ne compare que les lignes qui existent dans les deux comptages
        common_keys = set(counting_details_1.keys()) & set(counting_details_2.keys())
        
        discrepancy_count = 0
        
        # Comparer chaque ligne commune entre les deux comptages
        for key in common_keys:
            detail_1 = counting_details_1.get(key)
            detail_2 = counting_details_2.get(key)
            
            # Les deux détails existent forcément car on utilise l'intersection
            quantity_1 = detail_1.quantity_inventoried
            quantity_2 = detail_2.quantity_inventoried
            
            # Si les quantités diffèrent, c'est un écart
            if quantity_1 != quantity_2:
                discrepancy_count += 1
        
        # Calculer le taux d'écart
        # Le taux est basé uniquement sur les lignes communes aux deux comptages
        common_lines_count = len(common_keys)
        if common_lines_count > 0:
            discrepancy_rate = (discrepancy_count / common_lines_count) * 100
        else:
            discrepancy_rate = 0.0
        
        return {
            'discrepancy_count': discrepancy_count,
            'discrepancy_rate': round(discrepancy_rate, 2),
            'total_lines_counting_1': total_lines_counting_1,
            'total_lines_counting_2': total_lines_counting_2,
            'common_lines_count': common_lines_count,
        }

