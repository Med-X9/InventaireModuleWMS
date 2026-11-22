"""
Dispatcher Strategy : choix du service de lancement du comptage suivant.

- MAGASIN à plusieurs comptages → MagasinCountingLaunchService (écart par emplacement)
- Tous les autres (GENERAL, TOURNANT, …) → CountingLaunchService, inchangé
"""
from typing import Optional

from ..models import Job
from ..services.counting_launch_service import CountingLaunchService
from ..services.magasin_counting_launch_service import MagasinCountingLaunchService
from ..utils.counting_layout import uses_location_ecart


class CountingLaunchDispatcher:
    """Sélectionne la stratégie de lancement (Open/Closed)."""

    def get_service_for_inventory(self, inventory) -> CountingLaunchService:
        if inventory is not None and uses_location_ecart(inventory):
            return MagasinCountingLaunchService()
        return CountingLaunchService()

    def get_service_for_job(
        self, job_id: Optional[int], default: Optional[CountingLaunchService] = None
    ) -> CountingLaunchService:
        """
        Service adapté au job. Job introuvable ou invalide : service par défaut
        (c'est lui qui lèvera l'erreur métier habituelle).
        """
        fallback = default or CountingLaunchService()
        if not job_id or job_id <= 0:
            return fallback
        job = Job.objects.select_related('inventory').filter(id=job_id).first()
        if job is None:
            return fallback
        if uses_location_ecart(job.inventory):
            return MagasinCountingLaunchService()
        return fallback
