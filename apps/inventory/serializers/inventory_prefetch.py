"""
Helpers serializers inventaire — accès aux relations préchargées (anti N+1).
"""
from __future__ import annotations

from typing import Any, List, Optional

from apps.inventory.models import Assigment, Counting, Setting


def get_inventory_settings(inventory: Any) -> List[Setting]:
    """
    Retourne les Settings d'un inventaire en privilégiant le prefetch `awi_links`.

    Si le queryset a été préchargé via InventoryService.get_inventories_queryset_optimized,
    aucune requête supplémentaire n'est émise.
    """
    cache = getattr(inventory, "_prefetched_objects_cache", None)
    if cache is not None and "awi_links" in cache:
        return list(inventory.awi_links.all())
    return list(
        Setting.objects.filter(inventory=inventory).select_related(
            "account", "warehouse"
        )
    )


def get_first_inventory_setting(inventory: Any) -> Optional[Setting]:
    """Retourne le premier Setting (compte / entrepôt) de l'inventaire."""
    settings = get_inventory_settings(inventory)
    return settings[0] if settings else None


def get_inventory_countings(inventory: Any) -> List[Counting]:
    """
    Retourne les comptages ordonnés, via prefetch `countings` si disponible.
    """
    cache = getattr(inventory, "_prefetched_objects_cache", None)
    if cache is not None and "countings" in cache:
        return sorted(list(inventory.countings.all()), key=lambda c: c.order)
    return list(
        Counting.objects.filter(inventory=inventory).order_by("order")
    )


def get_inventory_assignments(inventory: Any) -> List[Assigment]:
    """
    Retourne les assignments liés aux jobs de l'inventaire.

    Préfère le prefetch `job_set__assigment_set` si présent, sinon requête dédiée.
    """
    cache = getattr(inventory, "_prefetched_objects_cache", None)
    if cache is not None and "job_set" in cache:
        assignments: List[Assigment] = []
        for job in inventory.job_set.all():
            job_cache = getattr(job, "_prefetched_objects_cache", None)
            if job_cache is not None and "assigment_set" in job_cache:
                assignments.extend(list(job.assigment_set.all()))
            else:
                assignments.extend(list(job.assigment_set.all()))
        return assignments
    return list(
        Assigment.objects.filter(job__inventory=inventory).select_related(
            "session", "counting"
        )
    )
