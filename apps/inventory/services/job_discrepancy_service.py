"""
Service pour calculer les écarts entre le 1er et le 2ème comptage d'un job.
"""
from typing import Dict, Any, List, Optional
import logging

from ..repositories.job_repository import JobRepository
from ..repositories.ecart_comptage_repository import EcartComptageRepository
from ..models import Job

logger = logging.getLogger(__name__)


class JobDiscrepancyService:
    """
    Service pour calculer les écarts entre les comptages et exposer
    différentes vues métiers des jobs avec écart.
    """

    def __init__(
        self,
        job_repository: Optional[JobRepository] = None,
        ecart_repository: Optional[EcartComptageRepository] = None,
    ) -> None:
        """
        Initialise le service avec ses repositories.

        Args:
            job_repository: Repository pour l'accès aux données des jobs.
            ecart_repository: Repository pour l'accès aux écarts de comptage.
        """
        self.job_repository = job_repository or JobRepository()
        self.ecart_repository = ecart_repository or EcartComptageRepository()

    def get_jobs_with_discrepancies(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Récupère les jobs avec leurs assignments et calcule les écarts
        entre le 1er et 2ème comptage.

        Args:
            inventory_id: ID de l'inventaire.
            warehouse_id: ID de l'entrepôt.

        Returns:
            Liste de dictionnaires contenant les informations des jobs avec
            écarts calculés.

        Raises:
            ValueError: Si l'inventaire ou le warehouse n'existe pas.
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
            warehouse_id=warehouse_id,
        )

        result: List[Dict[str, Any]] = []
        for job in jobs:
            # Récupérer les assignments du job
            assignments = self.job_repository.get_assignments_by_job(job)

            # Calculer les écarts entre le 1er et 2ème comptage
            discrepancy_info = self._calculate_discrepancies(job)

            # Formater les assignments
            assignments_data = [
                {
                    "id": assignment.id,
                    "reference": assignment.reference,
                    "status": assignment.status,
                    "counting_reference": assignment.counting.reference
                    if assignment.counting
                    else None,
                    "counting_order": assignment.counting.order
                    if assignment.counting
                    else None,
                    "personne_nom": (
                        f"{assignment.personne.nom} {assignment.personne.prenom}"
                        if assignment.personne
                        else None
                    ),
                    "personne_two_nom": (
                        f"{assignment.personne_two.nom} {assignment.personne_two.prenom}"
                        if assignment.personne_two
                        else None
                    ),
                }
                for assignment in assignments
            ]

            result.append(
                {
                    "job_id": job.id,
                    "job_reference": job.reference,
                    "job_status": job.status,
                    "assignments": assignments_data,
                    "discrepancy_count": discrepancy_info["discrepancy_count"],
                    "discrepancy_rate": discrepancy_info["discrepancy_rate"],
                    "total_lines_counting_1": discrepancy_info[
                        "total_lines_counting_1"
                    ],
                    "total_lines_counting_2": discrepancy_info[
                        "total_lines_counting_2"
                    ],
                    "common_lines_count": discrepancy_info["common_lines_count"],
                }
            )

        return result

    def get_jobs_with_unresolved_discrepancies_grouped_by_counting(
        self,
        inventory_id: int,
        warehouse_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Récupère les jobs qui ont au moins un écart de comptage non résolu,
        puis les regroupe par comptage (order).

        Règle métier :
        - On part des CountingDetail liés à un EcartComptage.
        - On exclut tous les détails où l'écart associé a un résultat final non nul
          ET resolved=True (écart déjà résolu avec un résultat final).
        - On groupe ensuite les jobs par comptage (counting.order).

        Returns:
            Liste de dictionnaires du type :
            [
                {
                    "counting_order": 3,
                    "jobs": [
                        {"job_id": 1, "job_reference": "job-1"},
                        ...
                    ],
                },
                ...
            ]
        """
        # Vérifier que l'inventaire existe
        inventory = self.job_repository.get_inventory_by_id(inventory_id)
        if not inventory:
            raise ValueError(f"Inventaire avec l'ID {inventory_id} non trouvé")

        # Vérifier que le warehouse existe
        warehouse = self.job_repository.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            raise ValueError(f"Warehouse avec l'ID {warehouse_id} non trouvé")

        # Récupérer les CountingDetail avec écarts non résolus
        details = self.ecart_repository.get_unresolved_counting_details_by_inventory_and_warehouse(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id,
        )

        grouped: Dict[int, Dict[str, Any]] = {}

        for detail in details:
            counting = detail.counting
            job = detail.job

            if not counting or not job:
                continue

            order = counting.order
            if order is None:
                continue

            if order not in grouped:
                grouped[order] = {
                    "counting_order": order,
                    "jobs": {},
                }

            jobs_by_id: Dict[int, Dict[str, Any]] = grouped[order]["jobs"]
            if job.id not in jobs_by_id:
                jobs_by_id[job.id] = {
                    "job_id": job.id,
                    "job_reference": job.reference,
                }

        # Transformer le dictionnaire interne de jobs (par id) en liste
        response: List[Dict[str, Any]] = []
        for order in sorted(grouped.keys()):
            jobs_list = list(grouped[order]["jobs"].values())
            response.append(
                {
                    "counting_order": order,
                    "jobs": jobs_list,
                }
            )

        return response

    def _calculate_discrepancies(self, job: Job) -> Dict[str, Any]:
        """
        Calcule les écarts entre le 1er et le 2ème comptage pour un job.

        Args:
            job: Job avec les counting details préchargés.

        Returns:
            Dictionnaire contenant :
            - discrepancy_count: Nombre de lignes avec écart
              (lignes communes avec quantités différentes).
            - discrepancy_rate: Taux d'écart (en pourcentage) basé sur les
              lignes communes aux deux comptages.
            - total_lines_counting_1: Nombre total de lignes du 1er comptage.
            - total_lines_counting_2: Nombre total de lignes du 2ème comptage.
            - common_lines_count: Nombre de lignes communes aux deux comptages.
        """
        # Récupérer les counting details depuis les attributs temporaires
        counting_details_1 = getattr(job, "_counting_details_1", {})
        counting_details_2 = getattr(job, "_counting_details_2", {})

        total_lines_counting_1 = len(counting_details_1)
        total_lines_counting_2 = len(counting_details_2)

        # Créer un ensemble des clés communes aux deux comptages (intersection)
        # On ne compare que les lignes qui existent dans les deux comptages
        common_keys = set(counting_details_1.keys()) & set(
            counting_details_2.keys()
        )

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
            "discrepancy_count": discrepancy_count,
            "discrepancy_rate": round(discrepancy_rate, 2),
            "total_lines_counting_1": total_lines_counting_1,
            "total_lines_counting_2": total_lines_counting_2,
            "common_lines_count": common_lines_count,
        }

