#!/usr/bin/env python3
"""
Clôture un assignment via l'API mobile.

  POST /mobile/api/job/<job_id>/close/<assignment_id>/
  Body JSON: { "personnes": [<id1>, <id2>] }  (1 à 2 personnes)

L'utilisateur JWT doit être celui affecté à l'assignment (session mobile), sinon 403.

Usage (depuis la racine du dépôt, venv activé) :

  python scripts/close_mobile_assignment.py

  python scripts/close_mobile_assignment.py --job-id 4 --assignment-id 8 --personnes 4 5

  python scripts/close_mobile_assignment.py --base-url http://127.0.0.1:9000 --username equipe-2001 --password user1234
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    import requests
except ImportError:
    print("Installez requests: pip install requests", file=sys.stderr)
    sys.exit(1)

DEFAULT_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:9000")
DEFAULT_USERNAME = "equipe-2001"
DEFAULT_PASSWORD = "user1234"
# Valeurs demandées par défaut
DEFAULT_JOB_ID = 4
DEFAULT_ASSIGNMENT_ID = 8
DEFAULT_PERSONNES: List[int] = [4, 5]


def login(base_url: str, username: str, password: str) -> str:
    url = f"{base_url.rstrip('/')}/mobile/api/auth/login/"
    r = requests.post(
        url,
        json={"username": username, "password": password},
        timeout=30,
    )
    r.raise_for_status()
    body = r.json()
    if not body.get("success"):
        raise RuntimeError(body.get("message") or str(body))
    data = body.get("data") or body
    token = data.get("access")
    if not token:
        raise RuntimeError("Token 'access' absent dans la réponse de login")
    return str(token)


def close_assignment(
    base_url: str,
    token: str,
    job_id: int,
    assignment_id: int,
    personnes: List[int],
) -> requests.Response:
    url = f"{base_url.rstrip('/')}/mobile/api/job/{job_id}/close/{assignment_id}/"
    return requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"personnes": personnes},
        timeout=120,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clôture assignment (API mobile CloseJobView)"
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--job-id", type=int, default=DEFAULT_JOB_ID)
    parser.add_argument("--assignment-id", type=int, default=DEFAULT_ASSIGNMENT_ID)
    parser.add_argument(
        "--personnes",
        type=int,
        nargs="+",
        default=DEFAULT_PERSONNES,
        metavar="ID",
        help="IDs Personne (1 à 2 valeurs, défaut: 4 5)",
    )
    args = parser.parse_args()

    if len(args.personnes) < 1 or len(args.personnes) > 2:
        print("Indiquez 1 ou 2 IDs dans --personnes", file=sys.stderr)
        return 1

    print(
        f"Clôture job_id={args.job_id} assignment_id={args.assignment_id} "
        f"personnes={args.personnes}"
    )
    token = login(args.base_url, args.username, args.password)
    r = close_assignment(
        args.base_url,
        token,
        args.job_id,
        args.assignment_id,
        list(args.personnes),
    )
    print("HTTP", r.status_code)
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r.text)
    return 0 if r.status_code in (200, 201) else 1


if __name__ == "__main__":
    raise SystemExit(main())
