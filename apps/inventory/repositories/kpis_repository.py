"""
Repository KPI magasin — accès aux données (requêtes ORM).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from django.db.models import Q, QuerySet

from apps.masterdata.models import Warehouse

from ..models import Assigment, ComptageSequence, Counting, EcartComptage, Inventory, Job, JobDetail
from .job_repository import JobRepository

ASSIGNMENT_EN_ATTENTE = ('EN ATTENTE', 'AFFECTE', 'PRET', 'TRANSFERT')
ASSIGNMENT_EN_COURS = ('ENTAME', 'DEBLOQUE', 'BLOQUE')
ASSIGNMENT_TERMINE = ('TERMINE',)


def team_key_from_assignment(assignment: Assigment) -> str:
    if assignment.session_id:
        return f"session:{assignment.session_id}"
    return f"persons:{assignment.personne_id or 0}:{assignment.personne_two_id or 0}"


def bucket_for_status(status: str) -> str:
    if status in ASSIGNMENT_EN_ATTENTE:
        return 'en_attente'
    if status in ASSIGNMENT_EN_COURS:
        return 'en_cours'
    if status in ASSIGNMENT_TERMINE:
        return 'termine'
    return 'en_attente'


@dataclass
class WarehouseKpiContext:
    inventory_id: int
    warehouse_id: int
    warehouse_name: str
    jobs_qs: QuerySet
    assignments_qs: QuerySet


class KpisRepository:
    """Requêtes ORM pour les indicateurs magasin."""

    def __init__(self, job_repository: Optional[JobRepository] = None) -> None:
        self._job_repository = job_repository or JobRepository()

    def get_inventory(self, inventory_id: int) -> Optional[Inventory]:
        return self._job_repository.get_inventory_by_id(inventory_id)

    def get_warehouse(self, warehouse_id: int) -> Optional[Warehouse]:
        return self._job_repository.get_warehouse_by_id(warehouse_id)

    def build_context(self, inventory_id: int, warehouse_id: int) -> WarehouseKpiContext:
        warehouse = self.get_warehouse(warehouse_id)
        return WarehouseKpiContext(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id,
            warehouse_name=warehouse.warehouse_name if warehouse else '',
            jobs_qs=Job.objects.filter(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id,
            ),
            assignments_qs=Assigment.objects.filter(
                job__inventory_id=inventory_id,
                job__warehouse_id=warehouse_id,
            ).select_related('session', 'counting', 'personne', 'personne_two'),
        )

    def count_jobs_total(self, ctx: WarehouseKpiContext) -> int:
        return ctx.jobs_qs.count()

    def count_jobs_affected(self, ctx: WarehouseKpiContext) -> int:
        return ctx.jobs_qs.filter(assigment__isnull=False).distinct().count()

    def count_locations_covered(self, ctx: WarehouseKpiContext) -> int:
        return (
            JobDetail.objects.filter(job__in=ctx.jobs_qs)
            .values('location_id')
            .distinct()
            .count()
        )

    def counting_ids_for_order(self, inventory_id: int, order: int) -> List[int]:
        return list(
            Counting.objects.filter(inventory_id=inventory_id, order=order).values_list(
                'id', flat=True
            )
        )

    def count_jobs_eligible_for_counting(
        self, ctx: WarehouseKpiContext, counting_ids: List[int]
    ) -> int:
        if not counting_ids:
            return 0
        return ctx.jobs_qs.filter(assigment__counting_id__in=counting_ids).distinct().count()

    def count_jobs_finished_for_counting(
        self, ctx: WarehouseKpiContext, counting_ids: List[int]
    ) -> int:
        if not counting_ids:
            return 0
        return ctx.jobs_qs.filter(
            id__in=Assigment.objects.filter(
                counting_id__in=counting_ids,
                status='TERMINE',
            ).values_list('job_id', flat=True),
        ).distinct().count()

    def assignment_status_counts(
        self, assignments_qs: QuerySet, order_filter: Q
    ) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for row in assignments_qs.filter(order_filter).values('status'):
            counts[bucket_for_status(row['status'])] += 1
        return dict(counts)

    def count_assignments(self, assignments_qs: QuerySet, order_filter: Q) -> int:
        return assignments_qs.filter(order_filter).count()

    def ecarts_queryset(self, inventory_id: int, warehouse_id: int) -> QuerySet:
        return EcartComptage.objects.filter(
            inventory_id=inventory_id,
            counting_sequences__counting_detail__job__warehouse_id=warehouse_id,
        ).distinct()

    def count_ecarts(self, inventory_id: int, warehouse_id: int) -> int:
        return self.ecarts_queryset(inventory_id, warehouse_id).count()

    def count_open_ecarts(self, inventory_id: int, warehouse_id: int) -> int:
        return (
            self.ecarts_queryset(inventory_id, warehouse_id)
            .filter(resolved=False)
            .count()
        )

    def count_jobs_with_ecart(self, ctx: WarehouseKpiContext) -> int:
        job_ids = list(
            ComptageSequence.objects.filter(
                ecart_comptage__inventory_id=ctx.inventory_id,
                counting_detail__job__warehouse_id=ctx.warehouse_id,
            )
            .values_list('counting_detail__job_id', flat=True)
            .distinct()
        )
        return ctx.jobs_qs.filter(id__in=job_ids).distinct().count()

    def count_locations_with_ecart(self, inventory_id: int, warehouse_id: int) -> int:
        location_ids = ComptageSequence.objects.filter(
            ecart_comptage__inventory_id=inventory_id,
            counting_detail__job__warehouse_id=warehouse_id,
        ).values_list('counting_detail__location_id', flat=True).distinct()
        return len(set(location_ids))

    def build_assignment_team_map(
        self, assignments_qs: QuerySet
    ) -> Tuple[Dict[Tuple[int, int], str], Dict[str, Optional[str]]]:
        team_map: Dict[Tuple[int, int], str] = {}
        usernames: Dict[str, Optional[str]] = {}
        for assignment in assignments_qs:
            tk = team_key_from_assignment(assignment)
            team_map[(assignment.job_id, assignment.counting_id)] = tk
            if tk not in usernames:
                if assignment.session_id and assignment.session:
                    usernames[tk] = assignment.session.username
                else:
                    usernames[tk] = None
        return team_map, usernames

    def team_assignment_stats(
        self, assignments_qs: QuerySet, counting_order: int
    ) -> Dict[str, Dict]:
        stats: Dict[str, Dict] = defaultdict(
            lambda: {'total': 0, 'termines': 0, 'buckets': defaultdict(int)}
        )
        for assignment in assignments_qs.filter(counting__order=counting_order):
            tk = team_key_from_assignment(assignment)
            stats[tk]['total'] += 1
            if assignment.status == 'TERMINE':
                stats[tk]['termines'] += 1
            stats[tk]['buckets'][bucket_for_status(assignment.status)] += 1
        return dict(stats)

    def count_distinct_teams(self, assignments_qs: QuerySet) -> int:
        return len({team_key_from_assignment(a) for a in assignments_qs})

    def link_ecarts_to_teams(
        self,
        inventory_id: int,
        warehouse_id: int,
        team_map: Dict[Tuple[int, int], str],
        open_only: bool = False,
    ) -> Tuple[Dict[str, Set[int]], Dict[str, Set[int]]]:
        ecart_filter = Q(
            ecart_comptage__inventory_id=inventory_id,
            counting_detail__job__warehouse_id=warehouse_id,
        )
        if open_only:
            ecart_filter &= Q(ecart_comptage__resolved=False)

        sequences = ComptageSequence.objects.filter(ecart_filter).values(
            'ecart_comptage_id',
            'counting_detail__job_id',
            'counting_detail__counting_id',
        )

        ecarts_by_team: Dict[str, Set[int]] = defaultdict(set)
        jobs_by_team: Dict[str, Set[int]] = defaultdict(set)

        for row in sequences:
            tk = team_map.get(
                (row['counting_detail__job_id'], row['counting_detail__counting_id'])
            )
            if not tk:
                continue
            ecarts_by_team[tk].add(row['ecart_comptage_id'])
            jobs_by_team[tk].add(row['counting_detail__job_id'])

        return dict(ecarts_by_team), dict(jobs_by_team)
