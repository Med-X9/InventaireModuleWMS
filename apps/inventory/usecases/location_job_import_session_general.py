"""
Strategy sessions import location-jobs pour inventaire GENERAL.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from apps.inventory.interfaces.location_job_import_session_strategy_interface import (
    ILocationJobImportSessionStrategy,
)


class LocationJobImportSessionGeneralStrategy(ILocationJobImportSessionStrategy):
    """
    Logique historique GENERAL :
    - Colonnes : warehouse, emplacement, active, job, session_1, session_2
    - session_2 obligatoire si active
    - Cohérence session_1/session_2 par job
    - Même équipe sur les deux sessions (1001↔2001, etc.)
    """

    def strategy_key(self) -> str:
        return "general_dual_session"

    def required_columns(self) -> List[str]:
        return [
            "warehouse",
            "emplacement",
            "active",
            "job",
            "session_1",
            "session_2",
        ]

    def session_2_required(self) -> bool:
        return True

    def validate_cross_job_rules(
        self,
        validated_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        errors: List[Dict[str, Any]] = []
        errors.extend(self._validate_job_sessions_consistency(validated_data))
        errors.extend(self._validate_job_single_team_in_sessions(validated_data))
        return errors

    def _validate_job_sessions_consistency(
        self, validated_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
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
                    "session_1": data.get("session_1", ""),
                    "session_2": data.get("session_2", ""),
                    "row_number": data.get("row_number"),
                }
            )

        for job, sessions_list in jobs_sessions.items():
            if len(sessions_list) <= 1:
                continue
            first = sessions_list[0]
            first_row = first["row_number"]
            for session_info in sessions_list[1:]:
                if (
                    session_info["session_1"] != first["session_1"]
                    or session_info["session_2"] != first["session_2"]
                ):
                    errors.append(
                        {
                            "row_number": session_info["row_number"],
                            "field": "session",
                            "value": (
                                f"session_1={session_info['session_1']}, "
                                f"session_2={session_info['session_2']}"
                            ),
                            "message": (
                                f"Le job '{job}' a des sessions incohérentes. "
                                f"Sessions attendues (ligne {first_row}): "
                                f"session_1='{first['session_1']}', "
                                f"session_2='{first['session_2']}'. "
                                f"Trouvées: session_1='{session_info['session_1']}', "
                                f"session_2='{session_info['session_2']}'"
                            ),
                        }
                    )
        return errors

    def _validate_job_single_team_in_sessions(
        self, validated_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        errors: List[Dict[str, Any]] = []
        pattern = re.compile(r"^equipe-(\d+)$", re.IGNORECASE)

        for data in validated_data:
            if not data.get("is_active"):
                continue
            session_1 = data.get("session_1") or ""
            session_2 = data.get("session_2") or ""
            if not session_1 or not session_2:
                continue

            match_1 = pattern.match(session_1)
            match_2 = pattern.match(session_2)
            if not match_1 or not match_2:
                continue

            num_1 = int(match_1.group(1))
            num_2 = int(match_2.group(1))
            if num_1 < 1001 or num_1 > 1999 or num_2 < 2001 or num_2 > 2999:
                continue

            real_team_1 = num_1 - 1000
            real_team_2 = num_2 - 2000

            if real_team_1 != real_team_2:
                errors.append(
                    {
                        "row_number": data.get("row_number"),
                        "field": "session",
                        "value": f"session_1={session_1}, session_2={session_2}",
                        "message": (
                            f"Le job '{data.get('job')}' doit être affecté à une seule "
                            f"équipe dans les deux sessions. "
                            f"Session 1: '{session_1}' (équipe {real_team_1}), "
                            f"Session 2: '{session_2}' (équipe {real_team_2}). "
                            f"Exemple valide: session_1='equipe-1001' et "
                            f"session_2='equipe-2001'"
                        ),
                    }
                )
        return errors
