"""
Service KPI magasin — logique métier (catalogue INVENTORY_KPI_CATALOG.md).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Tuple, TypedDict

from django.db.models import Q

from ..exceptions.job_exceptions import JobCreationError
from ..repositories.kpis_repository import KpisRepository, WarehouseKpiContext


class _KpiMeta(TypedDict):
    slug: str
    label: str
    data_key: str


# Métadonnées réponse API par ID catalogue (cf. docs/INVENTORY_KPI_CATALOG.md)
_KPI_BY_CATALOG_ID: Dict[str, _KpiMeta] = {
    'KPI-A01': {'slug': 'nombre-jobs-total', 'label': 'Nombre total de jobs', 'data_key': 'nombre_jobs_total'},
    'KPI-A02': {'slug': 'nombre-jobs-affectes', 'label': 'Nombre de jobs affectés', 'data_key': 'nombre_jobs_affectes'},
    'KPI-A03': {'slug': 'nombre-emplacements-couverts', 'label': "Nombre d'emplacements couverts", 'data_key': 'nombre_emplacements_couverts'},
    'KPI-B01': {'slug': 'taux-jobs-termines-1er-comptage', 'label': 'Taux de jobs terminés — 1er comptage', 'data_key': 'taux_jobs_termines_1er_comptage'},
    'KPI-B02': {'slug': 'taux-jobs-termines-2e-comptage', 'label': 'Taux de jobs terminés — 2e comptage', 'data_key': 'taux_jobs_termines_2e_comptage'},
    'KPI-C01': {'slug': 'repartition-assignments-1er-comptage', 'label': 'Répartition des assignments — 1er comptage', 'data_key': 'repartition_assignments_1er_comptage'},
    'KPI-C02': {'slug': 'repartition-assignments-2e-comptage', 'label': 'Répartition des assignments — 2e comptage', 'data_key': 'repartition_assignments_2e_comptage'},
    'KPI-C03': {'slug': 'repartition-assignments-3e-comptage', 'label': 'Répartition des assignments — 3e comptage', 'data_key': 'repartition_assignments_3e_comptage'},
    'KPI-C04': {'slug': 'repartition-assignments-nieme-comptage', 'label': 'Répartition des assignments — comptages suivants (4e et +)', 'data_key': 'repartition_assignments_nieme_comptage'},
    'KPI-D01': {'slug': 'nombre-ecarts', 'label': "Nombre d'écarts sur le magasin", 'data_key': 'nombre_ecarts'},
    'KPI-D02': {'slug': 'nombre-jobs-avec-ecart', 'label': 'Nombre de jobs contenant un écart', 'data_key': 'nombre_jobs_avec_ecart'},
    'KPI-D03': {'slug': 'nombre-emplacements-avec-ecart', 'label': "Nombre d'emplacements contenant un écart", 'data_key': 'nombre_emplacements_avec_ecart'},
    'KPI-D04': {'slug': 'nombre-ecarts-ouverts', 'label': "Nombre d'écarts ouverts", 'data_key': 'nombre_ecarts_ouverts'},
    'KPI-T01': {'slug': 'nombre-equipes', 'label': "Nombre d'équipes distinctes", 'data_key': 'nombre_equipes'},
    'KPI-T02': {'slug': 'taux-termine-1er-comptage-par-equipe', 'label': 'Taux terminé — 1er comptage par équipe', 'data_key': 'taux_termine_1er_comptage_par_equipe'},
    'KPI-T03': {'slug': 'taux-termine-2e-comptage-par-equipe', 'label': 'Taux terminé — 2e comptage par équipe', 'data_key': 'taux_termine_2e_comptage_par_equipe'},
    'KPI-T04': {'slug': 'repartition-1er-comptage-par-equipe', 'label': 'Répartition 1er comptage par équipe', 'data_key': 'repartition_1er_comptage_par_equipe'},
    'KPI-T05': {'slug': 'repartition-2e-comptage-par-equipe', 'label': 'Répartition 2e comptage par équipe', 'data_key': 'repartition_2e_comptage_par_equipe'},
    'KPI-T06': {'slug': 'equipes-multi-ecarts', 'label': 'Équipes avec au moins 2 écarts ouverts', 'data_key': 'equipes_multi_ecarts'},
    'KPI-T07': {'slug': 'jobs-avec-ecart-par-equipe', 'label': 'Nombre de jobs avec écart par équipe', 'data_key': 'jobs_avec_ecart_par_equipe'},
}


def _percent(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(count / total * 100, 2)


def _bucket_payload(
    counts: Dict[str, int], total: int
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    return (
        {'count': counts.get('en_attente', 0), 'percent': _percent(counts.get('en_attente', 0), total)},
        {'count': counts.get('en_cours', 0), 'percent': _percent(counts.get('en_cours', 0), total)},
        {'count': counts.get('termine', 0), 'percent': _percent(counts.get('termine', 0), total)},
    )


class KpisService:
    """Calcule les 20 indicateurs pour un inventaire / magasin."""

    def __init__(self, repository: KpisRepository | None = None) -> None:
        self.repository = repository or KpisRepository()

    def _validate_and_build_context(
        self, inventory_id: int, warehouse_id: int
    ) -> WarehouseKpiContext:
        if not self.repository.get_inventory(inventory_id):
            raise JobCreationError(f"Inventaire avec l'ID {inventory_id} non trouvé")
        if not self.repository.get_warehouse(warehouse_id):
            raise JobCreationError(f"Entrepôt avec l'ID {warehouse_id} non trouvé")
        return self.repository.build_context(inventory_id, warehouse_id)

    def _build_meta(self, ctx: WarehouseKpiContext, kpi: _KpiMeta) -> Dict[str, Any]:
        return {
            'inventory_id': ctx.inventory_id,
            'warehouse_id': ctx.warehouse_id,
            'warehouse_name': ctx.warehouse_name,
            'kpi': kpi['slug'],
            'label': kpi['label'],
            'generated_at': datetime.now(timezone.utc).isoformat(),
        }

    def _wrap(self, ctx: WarehouseKpiContext, catalog_id: str, value: Any) -> Dict[str, Any]:
        kpi = _KPI_BY_CATALOG_ID[catalog_id]
        return {'meta': self._build_meta(ctx, kpi), 'data': {kpi['data_key']: value}}

    def _jobs_termines_payload(self, ctx: WarehouseKpiContext, order: int) -> Dict[str, Any]:
        counting_ids = self.repository.counting_ids_for_order(ctx.inventory_id, order)
        eligibles = self.repository.count_jobs_eligible_for_counting(ctx, counting_ids)
        termines = self.repository.count_jobs_finished_for_counting(ctx, counting_ids)
        return {
            'counting_order': order,
            'jobs_termines': termines,
            'jobs_eligibles': eligibles,
            'percent': _percent(termines, eligibles),
        }

    def _assignment_distribution(
        self, ctx: WarehouseKpiContext, order_filter: Q, counting_order: int
    ) -> Dict[str, Any]:
        total = self.repository.count_assignments(ctx.assignments_qs, order_filter)
        bucket_counts = self.repository.assignment_status_counts(
            ctx.assignments_qs, order_filter
        )
        en_attente, en_cours, termine = _bucket_payload(bucket_counts, total)
        return {
            'counting_order': counting_order,
            'total_assignments': total,
            'en_attente': en_attente,
            'en_cours': en_cours,
            'termine': termine,
        }

    def _teams_rate_payload(self, ctx: WarehouseKpiContext, counting_order: int) -> Dict[str, Any]:
        _, usernames = self.repository.build_assignment_team_map(ctx.assignments_qs)
        stats = self.repository.team_assignment_stats(ctx.assignments_qs, counting_order)
        teams = []
        for tk in sorted(stats.keys()):
            s = stats[tk]
            teams.append(
                {
                    'team_key': tk,
                    'username': usernames.get(tk),
                    'percent': _percent(s['termines'], s['total']),
                    'termines': s['termines'],
                    'total': s['total'],
                }
            )
        return {'teams': teams}

    def _teams_distribution_payload(
        self, ctx: WarehouseKpiContext, counting_order: int
    ) -> Dict[str, Any]:
        _, usernames = self.repository.build_assignment_team_map(ctx.assignments_qs)
        stats = self.repository.team_assignment_stats(ctx.assignments_qs, counting_order)
        teams = []
        for tk in sorted(stats.keys()):
            s = stats[tk]
            total = s['total']
            buckets = dict(s.get('buckets', {}))
            en_a, en_c, te = _bucket_payload(buckets, total)
            teams.append(
                {
                    'team_key': tk,
                    'username': usernames.get(tk),
                    'counting_order': counting_order,
                    'en_attente': en_a,
                    'en_cours': en_c,
                    'termine': te,
                }
            )
        return {'teams': teams}

    def compute_nombre_jobs_total(self, inventory_id: int, warehouse_id: int) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(ctx, 'KPI-A01', self.repository.count_jobs_total(ctx))

    def compute_nombre_jobs_affectes(self, inventory_id: int, warehouse_id: int) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(ctx, 'KPI-A02', self.repository.count_jobs_affected(ctx))

    def compute_nombre_emplacements_couverts(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(ctx, 'KPI-A03', self.repository.count_locations_covered(ctx))

    def compute_taux_jobs_termines_1er_comptage(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(ctx, 'KPI-B01', self._jobs_termines_payload(ctx, 1))

    def compute_taux_jobs_termines_2e_comptage(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(ctx, 'KPI-B02', self._jobs_termines_payload(ctx, 2))

    def compute_repartition_assignments_1er_comptage(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(
            ctx, 'KPI-C01', self._assignment_distribution(ctx, Q(counting__order=1), 1)
        )

    def compute_repartition_assignments_2e_comptage(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(
            ctx, 'KPI-C02', self._assignment_distribution(ctx, Q(counting__order=2), 2)
        )

    def compute_repartition_assignments_3e_comptage(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(
            ctx, 'KPI-C03', self._assignment_distribution(ctx, Q(counting__order=3), 3)
        )

    def compute_repartition_assignments_nieme_comptage(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(
            ctx, 'KPI-C04', self._assignment_distribution(ctx, Q(counting__order__gte=4), 4)
        )

    def compute_nombre_ecarts(self, inventory_id: int, warehouse_id: int) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(
            ctx, 'KPI-D01', self.repository.count_ecarts(ctx.inventory_id, ctx.warehouse_id)
        )

    def compute_nombre_jobs_avec_ecart(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(ctx, 'KPI-D02', self.repository.count_jobs_with_ecart(ctx))

    def compute_nombre_emplacements_avec_ecart(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(
            ctx,
            'KPI-D03',
            self.repository.count_locations_with_ecart(ctx.inventory_id, ctx.warehouse_id),
        )

    def compute_nombre_ecarts_ouverts(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(
            ctx,
            'KPI-D04',
            self.repository.count_open_ecarts(ctx.inventory_id, ctx.warehouse_id),
        )

    def compute_nombre_equipes(self, inventory_id: int, warehouse_id: int) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(
            ctx, 'KPI-T01', self.repository.count_distinct_teams(ctx.assignments_qs)
        )

    def compute_taux_termine_1er_comptage_par_equipe(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(ctx, 'KPI-T02', self._teams_rate_payload(ctx, 1))

    def compute_taux_termine_2e_comptage_par_equipe(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(ctx, 'KPI-T03', self._teams_rate_payload(ctx, 2))

    def compute_repartition_1er_comptage_par_equipe(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(ctx, 'KPI-T04', self._teams_distribution_payload(ctx, 1))

    def compute_repartition_2e_comptage_par_equipe(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        return self._wrap(ctx, 'KPI-T05', self._teams_distribution_payload(ctx, 2))

    def compute_equipes_multi_ecarts(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        team_map, usernames = self.repository.build_assignment_team_map(ctx.assignments_qs)
        open_ecarts_by_team, _ = self.repository.link_ecarts_to_teams(
            ctx.inventory_id, ctx.warehouse_id, team_map, open_only=True
        )
        multi_keys = sorted(tk for tk, ids in open_ecarts_by_team.items() if len(ids) >= 2)
        teams = [
            {
                'team_key': tk,
                'username': usernames.get(tk),
                'open_discrepancies_count': len(open_ecarts_by_team.get(tk, set())),
                'is_multi_discrepancy': len(open_ecarts_by_team.get(tk, set())) >= 2,
            }
            for tk in sorted(open_ecarts_by_team.keys())
        ]
        return self._wrap(
            ctx,
            'KPI-T06',
            {'count': len(multi_keys), 'team_keys': multi_keys, 'teams': teams},
        )

    def compute_jobs_avec_ecart_par_equipe(
        self, inventory_id: int, warehouse_id: int
    ) -> Dict[str, Any]:
        ctx = self._validate_and_build_context(inventory_id, warehouse_id)
        team_map, usernames = self.repository.build_assignment_team_map(ctx.assignments_qs)
        _, jobs_by_team = self.repository.link_ecarts_to_teams(
            ctx.inventory_id, ctx.warehouse_id, team_map, open_only=False
        )
        teams = [
            {
                'team_key': tk,
                'username': usernames.get(tk),
                'jobs_with_discrepancy_count': len(job_ids),
            }
            for tk, job_ids in sorted(jobs_by_team.items())
        ]
        return self._wrap(ctx, 'KPI-T07', {'teams': teams})
