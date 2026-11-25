"""
Stratégie de lancement du comptage suivant (3e, 4e, …) pour un MAGASIN à plusieurs comptages.

Le service GENERAL (`CountingLaunchService`) reste inchangé. Cette stratégie en hérite pour
réutiliser la création du job detail, de l'assignment et du comptage cible, mais détermine
les emplacements concernés à partir de l'écart PAR EMPLACEMENT (une séquence par comptage,
sans notion de produit) au lieu des écarts par produit de GENERAL.
"""
from typing import List

from ..exceptions.counting_exceptions import CountingNotFoundError, CountingValidationError
from ..utils.location_ecart_results import location_ecart_results
from .counting_launch_service import CountingLaunchService


class MagasinCountingLaunchService(CountingLaunchService):
    """Lancement du comptage suivant pour un MAGASIN (écart par emplacement)."""

    def _ecart_results(self, job):
        """
        Écarts par emplacement de l'inventaire/entrepôt du job, calculés une seule fois par
        requête (le lancement d'un comptage ne modifie ni les saisies ni les résultats finaux).
        """
        cache = self._cache()
        key = ('location_ecart_results', job.inventory_id, job.warehouse_id)
        if key not in cache:
            cache[key] = location_ecart_results(job.inventory, warehouse_id=job.warehouse_id)
        return cache[key]

    def _get_job_or_raise(self, job_id: int):
        job = self._get_job(job_id)
        if not job:
            raise CountingNotFoundError(f"Job introuvable pour l'identifiant {job_id}.")
        return job

    def get_locations_with_discrepancy_for_job(self, job_id: int) -> List[int]:
        """
        Emplacements du job dont l'écart n'est pas tranché (résultat final vide) :
        ce sont ceux qui attendent le comptage suivant.
        """
        job = self._get_job_or_raise(job_id)
        results = self._ecart_results(job)
        return [
            location_id
            for location_id, info in results.items()
            if info['job_id'] == job.id and info['ecart'].final_result is None
        ]

    def launch_counting(self, job_id: int, location_id: int, session_id: int):
        """
        Vérifie l'écart par emplacement, puis délègue la création du comptage
        (job detail, assignment) au service de base.
        """
        job = self._get_job(job_id) if job_id and job_id > 0 else None
        if job is not None:
            info = self._ecart_results(job).get(location_id)
            if info is None or info['job_id'] != job.id or info['ecart'].final_result is not None:
                raise CountingValidationError(
                    "L'emplacement n'a pas d'écart non résolu (écart par emplacement : "
                    "le résultat final est déjà renseigné ou aucun comptage n'a été saisi). "
                    "Seuls les emplacements en écart peuvent avoir un nouveau comptage."
                )
        return super().launch_counting(job_id, location_id, session_id)
