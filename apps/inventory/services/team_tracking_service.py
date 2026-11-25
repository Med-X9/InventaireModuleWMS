"""
Suivi par équipe : jobs (affectations par comptage) de chaque équipe mobile avec leur statut.
"""
from collections import defaultdict
from typing import Any, Dict, List

from ..constants import AssignmentStatus
from ..models import Assigment

# Statuts de suivi affichés ; les statuts intermédiaires sont ramenés à l'un des quatre.
STATUS_EN_ATTENTE = 'EN ATTENTE'
STATUS_ENTAME = 'ENTAME'
STATUS_TERMINE = 'TERMINE'
STATUS_BLOQUE = 'BLOQUE'

_STATUS_BUCKET = {
    AssignmentStatus.EN_ATTENTE: STATUS_EN_ATTENTE,
    AssignmentStatus.AFFECTE: STATUS_EN_ATTENTE,
    AssignmentStatus.PRET: STATUS_EN_ATTENTE,
    AssignmentStatus.TRANSFERT: STATUS_EN_ATTENTE,
    AssignmentStatus.ENTAME: STATUS_ENTAME,
    AssignmentStatus.DEBLOQUE: STATUS_ENTAME,
    AssignmentStatus.TERMINE: STATUS_TERMINE,
    AssignmentStatus.BLOQUE: STATUS_BLOQUE,
}


class TeamTrackingService:
    def get_team_tracking(self, inventory_id: int, warehouse_id: int) -> List[Dict[str, Any]]:
        assignments = (
            Assigment.objects.filter(
                job__inventory_id=inventory_id,
                job__warehouse_id=warehouse_id,
                session__isnull=False,
            )
            .select_related('job', 'counting', 'session')
            .order_by('session__username', 'job__reference', 'counting__order')
        )

        teams: Dict[int, Dict[str, Any]] = {}
        for a in assignments:
            team = teams.get(a.session_id)
            if team is None:
                full_name = ' '.join(p for p in (a.session.prenom, a.session.nom) if p)
                team = teams[a.session_id] = {
                    'session_id': a.session_id,
                    'team': a.session.username,
                    'team_name': full_name or None,
                    'jobs': [],
                    'counts': defaultdict(int),
                }
            bucket = _STATUS_BUCKET.get(a.status, STATUS_EN_ATTENTE)
            team['counts'][bucket] += 1
            team['jobs'].append({
                'job_id': a.job_id,
                'job_reference': a.job.reference,
                'counting_order': a.counting.order if a.counting else None,
                'status': bucket,
            })

        result = []
        for team in teams.values():
            counts = team.pop('counts')
            team.update({
                'jobs_en_attente': counts[STATUS_EN_ATTENTE],
                'jobs_entame': counts[STATUS_ENTAME],
                'jobs_termine': counts[STATUS_TERMINE],
                'jobs_bloque': counts[STATUS_BLOQUE],
                'jobs_total': len(team['jobs']),
            })
            result.append(team)
        return result
