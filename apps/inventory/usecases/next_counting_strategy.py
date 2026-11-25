"""
Strategy : jobs à relancer, regroupés par prochain comptage (page « Lancement »).

- GENERAL (et autres) : calcul historique, inchangé (`JobDiscrepancyService`).
- EnVracNextCountingStrategy : MAGASIN à plusieurs comptages (écart par emplacement). Le prochain
  comptage se détermine EMPLACEMENT par EMPLACEMENT : un emplacement en écart (résultat final
  vide) dont le dernier comptage lancé est terminé attend le comptage suivant (n+1). Si ce
  comptage n+1 est déjà lancé (en attente), l'emplacement n'est plus proposé : un job lancé
  à n+1 n'apparaît donc jamais sous n.
"""
from collections import defaultdict
from typing import Any, Dict, List

from apps.inventory.constants import JobDetailStatus
from apps.inventory.models import JobDetail
from apps.inventory.utils.location_ecart_results import location_ecart_results


class EnVracNextCountingStrategy:
    """Regroupe les jobs par prochain comptage à lancer, par emplacement en écart."""

    def group_jobs(self, inventory, warehouse_id: int, jobs: List[Any]) -> List[Dict[str, Any]]:
        jobs_by_id = {job.id: job for job in jobs}
        if not jobs_by_id:
            return []

        results = location_ecart_results(inventory, warehouse_id=warehouse_id)
        unresolved = {
            location_id: info
            for location_id, info in results.items()
            if info['job_id'] in jobs_by_id and info['ecart'].final_result is None
        }
        if not unresolved:
            return []

        # Dernier comptage lancé par (job, emplacement) et son statut (une seule requête)
        highest: Dict[tuple, tuple] = {}
        rows = (
            JobDetail.objects.filter(
                job_id__in=jobs_by_id.keys(),
                location_id__in=unresolved.keys(),
                counting__isnull=False,
            )
            .exclude(status=JobDetailStatus.ANNULE)
            .values_list('job_id', 'location_id', 'counting__order', 'status')
        )
        for job_id, location_id, order, status in rows:
            key = (job_id, location_id)
            if key not in highest or order > highest[key][0]:
                highest[key] = (order, status)

        # (prochain comptage, job) -> nombre d'emplacements en attente de ce comptage
        needing: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        for location_id, info in unresolved.items():
            order_status = highest.get((info['job_id'], location_id))
            if not order_status:
                continue
            order, status = order_status
            # Comptages 1 et 2 terminés au minimum, et dernier comptage lancé terminé
            if order >= 2 and status == JobDetailStatus.TERMINE:
                needing[order + 1][info['job_id']] += 1

        grouped = []
        for next_order in sorted(needing):
            jobs_list = [
                {
                    'job_id': job_id,
                    'job_reference': jobs_by_id[job_id].reference,
                    'current_max_counting': next_order - 1,
                    'has_unresolved_discrepancies': True,
                    'discrepancies_locations_count': count,
                }
                for job_id, count in sorted(needing[next_order].items())
            ]
            grouped.append({'next_counting_order': next_order, 'jobs': jobs_list})
        return grouped
