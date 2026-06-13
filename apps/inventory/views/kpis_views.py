"""
Vues API KPI magasin — une APIView GET par indicateur.
"""
import logging
from typing import Callable

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..exceptions.job_exceptions import JobCreationError
from ..services.kpis_service import KpisService
from ..utils.response_utils import error_response, success_response

logger = logging.getLogger(__name__)


def _handle_kpi(
    inventory_id: int,
    warehouse_id: int,
    compute_fn: Callable,
    log_name: str,
    message: str,
) -> Response:
    try:
        payload = compute_fn(KpisService(), inventory_id, warehouse_id)
        return success_response(data=payload['data'], message=message, meta=payload['meta'])
    except JobCreationError as exc:
        logger.error('Erreur métier %s: %s', log_name, exc)
        return error_response(message=str(exc), status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        logger.error('Erreur inattendue %s: %s', log_name, exc)
        return error_response(
            message=f"Une erreur est survenue lors du calcul de l'indicateur: {exc}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class KpiNombreJobsTotalView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_nombre_jobs_total(i, w),
            'nombre-jobs-total',
            'Nombre total de jobs',
        )


class KpiNombreJobsAffectesView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_nombre_jobs_affectes(i, w),
            'nombre-jobs-affectes',
            'Nombre de jobs affectés',
        )


class KpiNombreEmplacementsCouvertsView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_nombre_emplacements_couverts(i, w),
            'nombre-emplacements-couverts',
            "Nombre d'emplacements couverts",
        )


class KpiTauxJobsTermines1erComptageView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_taux_jobs_termines_1er_comptage(i, w),
            'taux-jobs-termines-1er-comptage',
            'Taux de jobs terminés — 1er comptage',
        )


class KpiTauxJobsTermines2eComptageView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_taux_jobs_termines_2e_comptage(i, w),
            'taux-jobs-termines-2e-comptage',
            'Taux de jobs terminés — 2e comptage',
        )


class KpiRepartitionAssignments1erComptageView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_repartition_assignments_1er_comptage(i, w),
            'repartition-assignments-1er-comptage',
            'Répartition des assignments — 1er comptage',
        )


class KpiRepartitionAssignments2eComptageView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_repartition_assignments_2e_comptage(i, w),
            'repartition-assignments-2e-comptage',
            'Répartition des assignments — 2e comptage',
        )


class KpiRepartitionAssignments3eComptageView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_repartition_assignments_3e_comptage(i, w),
            'repartition-assignments-3e-comptage',
            'Répartition des assignments — 3e comptage',
        )


class KpiRepartitionAssignmentsNiemeComptageView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_repartition_assignments_nieme_comptage(i, w),
            'repartition-assignments-nieme-comptage',
            'Répartition des assignments — comptages suivants (4e et +)',
        )


class KpiNombreEcartsView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_nombre_ecarts(i, w),
            'nombre-ecarts',
            "Nombre d'écarts sur le magasin",
        )


class KpiNombreJobsAvecEcartView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_nombre_jobs_avec_ecart(i, w),
            'nombre-jobs-avec-ecart',
            'Nombre de jobs contenant un écart',
        )


class KpiNombreEmplacementsAvecEcartView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_nombre_emplacements_avec_ecart(i, w),
            'nombre-emplacements-avec-ecart',
            "Nombre d'emplacements contenant un écart",
        )


class KpiNombreEcartsOuvertsView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_nombre_ecarts_ouverts(i, w),
            'nombre-ecarts-ouverts',
            "Nombre d'écarts ouverts",
        )


class KpiNombreEquipesView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_nombre_equipes(i, w),
            'nombre-equipes',
            "Nombre d'équipes distinctes",
        )


class KpiTauxTermine1erComptageParEquipeView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_taux_termine_1er_comptage_par_equipe(i, w),
            'taux-termine-1er-comptage-par-equipe',
            'Taux terminé — 1er comptage par équipe',
        )


class KpiTauxTermine2eComptageParEquipeView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_taux_termine_2e_comptage_par_equipe(i, w),
            'taux-termine-2e-comptage-par-equipe',
            'Taux terminé — 2e comptage par équipe',
        )


class KpiRepartition1erComptageParEquipeView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_repartition_1er_comptage_par_equipe(i, w),
            'repartition-1er-comptage-par-equipe',
            'Répartition 1er comptage par équipe',
        )


class KpiRepartition2eComptageParEquipeView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_repartition_2e_comptage_par_equipe(i, w),
            'repartition-2e-comptage-par-equipe',
            'Répartition 2e comptage par équipe',
        )


class KpiEquipesMultiEcartsView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_equipes_multi_ecarts(i, w),
            'equipes-multi-ecarts',
            'Équipes avec au moins 2 écarts ouverts',
        )


class KpiJobsAvecEcartParEquipeView(APIView):
    http_method_names = ['get']

    def get(self, request, inventory_id: int, warehouse_id: int):
        return _handle_kpi(
            inventory_id,
            warehouse_id,
            lambda s, i, w: s.compute_jobs_avec_ecart_par_equipe(i, w),
            'jobs-avec-ecart-par-equipe',
            'Nombre de jobs avec écart par équipe',
        )
