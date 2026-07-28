"""
Strategy sessions import location-jobs pour MAGASIN / TOURNANT (mono-comptage).
"""
from __future__ import annotations

from typing import Any, Dict, List

from apps.inventory.interfaces.location_job_import_session_strategy_interface import (
    ILocationJobImportSessionStrategy,
)


class LocationJobImportSessionSingleStrategy(ILocationJobImportSessionStrategy):
    """
    Inventaires à un seul comptage :
    - Colonnes obligatoires : warehouse, emplacement, active, job, session_1
    - session_2 : optionnelle (colonne Excel et/ou valeur) — table DB déjà nullable
    - Cohérence : même session_1 pour toutes les lignes d'un même job
    - Pas de règle « même équipe » sur 2 sessions
    """

    def strategy_key(self) -> str:
        return "single_session"

    def required_columns(self) -> List[str]:
        return [
            "warehouse",
            "emplacement",
            "active",
            "job",
            "session_1",
        ]

    def session_2_required(self) -> bool:
        return False

    def validate_cross_job_rules(
        self,
        validated_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Cohérence session_1 seule par job."""
        errors: List[Dict[str, Any]] = []
        jobs_sessions: Dict[str, List[Dict[str, Any]]] = {}

        for data in validated_data:
            if not data.get("is_active"):
                continue
            job = data.get("job")
            if not job:
                continue
            jobs_sessions.setdefault(job, []).append(
                {
                    "session_1": data.get("session_1") or "",
                    "row_number": data.get("row_number"),
                }
            )

        for job, sessions_list in jobs_sessions.items():
            if len(sessions_list) <= 1:
                continue
            first = sessions_list[0]
            for session_info in sessions_list[1:]:
                if session_info["session_1"] != first["session_1"]:
                    errors.append(
                        {
                            "row_number": session_info["row_number"],
                            "field": "session_1",
                            "value": session_info["session_1"],
                            "message": (
                                f"Le job '{job}' a des session_1 incohérentes. "
                                f"Attendue (ligne {first['row_number']}): "
                                f"'{first['session_1']}'. "
                                f"Trouvée: '{session_info['session_1']}'"
                            ),
                        }
                    )
        return errors
