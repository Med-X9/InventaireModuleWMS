#!/usr/bin/env python3
"""
Envoie un lot de lignes de comptage (CountingDetail) vers l'API mobile,
par défaut **22 lignes** pour le job **JOB-0004** (jeu de données fourni).

  POST /mobile/api/job/<job_id>/counting-detail/

Prérequis:
  - Serveur Django joignable (ex. http://127.0.0.1:9000)
  - Utilisateur mobile (défaut: equipe-2001 / user1234)
  - Django disponible sur la machine pour résoudre job / emplacements / produits
    à partir des références (sinon utilisez les options --job-id, --counting-id, etc.)

Usage (depuis la racine du projet, avec venv activé) :

  python scripts/post_mobile_counting_detail.py

  python scripts/post_mobile_counting_detail.py --base-url http://127.0.0.1:9000

  # Autre comptage (clé primaire Counting), défaut = 2
  python scripts/post_mobile_counting_detail.py --counting-pk 3

  # Sélection par ordre de comptage au lieu de l'ID
  python scripts/post_mobile_counting_detail.py --counting-order 1

  python scripts/post_mobile_counting_detail.py --job-id 12 --counting-id 3 --assignment-id 45

Si rien ne s'enregistre en base, causes fréquentes (vérifiées avant l'envoi sauf --no-preflight) :
  - pas de JobDetail pour un emplacement sur le job + comptage → utiliser --filter-covered
  - comptage « par article » avec DLC / n_lot obligatoires → ajouter \"dlc\" / \"n_lot\" dans chaque ligne de DEFAULT_ROWS
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Répertoire racine du repo (parent de ce fichier = scripts/, parent.parent = projet Django)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    import requests
except ImportError:
    print("Installez requests: pip install requests", file=sys.stderr)
    sys.exit(1)


# 22 lignes (emplacement + code-barres + quantité) — job JOB-0004.
# Les quantités peuvent se répéter sur plusieurs emplacements (ex. 80, 1, 47, 74).
# Deux code-barres distincts : premier article seul sur LO101B001, le reste en 9312825662488.
DEFAULT_ROWS: List[Dict[str, Any]] = [
    {"location_ref": "LO101B001", "barcode": "8994993025626", "quantity": 5},
    {"location_ref": "LO101B002", "barcode": "9312825662488", "quantity": 15},
    {"location_ref": "LO101B003", "barcode": "9312825662488", "quantity": 70},
    {"location_ref": "LO101B004", "barcode": "9312825662488", "quantity": 1},
    {"location_ref": "LO101B005", "barcode": "9312825662488", "quantity": 46},
    {"location_ref": "LO101B006", "barcode": "9312825662488", "quantity": 8},
    {"location_ref": "LO101B007", "barcode": "9312825662488", "quantity": 77},
    {"location_ref": "LO101B008", "barcode": "9312825662488", "quantity": 47},
    {"location_ref": "LO101B009", "barcode": "9312825662488", "quantity": 746},
    {"location_ref": "LO101B010", "barcode": "9312825662488", "quantity": 9},
    {"location_ref": "LO101B011", "barcode": "9312825662488", "quantity": 80},
    {"location_ref": "LO101B012", "barcode": "9312825662488", "quantity": 90},
    {"location_ref": "LO101B013", "barcode": "9312825662488", "quantity": 4},
    {"location_ref": "LO101B014", "barcode": "9312825662488", "quantity": 368},
    {"location_ref": "LO101B015", "barcode": "9312825662488", "quantity": 80},
    {"location_ref": "LO101B016", "barcode": "9312825662488", "quantity": 1},
    {"location_ref": "LO101B017", "barcode": "9312825662488", "quantity": 7},
    {"location_ref": "LO101B018", "barcode": "9312825662488", "quantity": 47},
    {"location_ref": "LO101B019", "barcode": "9312825662488", "quantity": 74},
    {"location_ref": "LO101B020", "barcode": "9312825662488", "quantity": 74},
    {"location_ref": "LO101B021", "barcode": "9312825662488", "quantity": 90},
    {"location_ref": "LO101B022", "barcode": "9312825662488", "quantity": 142},
]

DEFAULT_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:9000")
DEFAULT_USERNAME = "equipe-2001"
DEFAULT_PASSWORD = "user1234"
DEFAULT_JOB_REF = "JOB-0004"
# ID (clé primaire) du modèle Counting pour choisir l'assignment en mode auto
DEFAULT_COUNTING_ID = 2


def setup_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
    import django

    if not (_PROJECT_ROOT / "manage.py").is_file():
        print(
            f"Arret: manage.py introuvable sous {_PROJECT_ROOT}.\n"
            "Lancez le script depuis le depot InventaireModuleWMS "
            f"(repertoire contenant apps/ et project/).",
            file=sys.stderr,
        )
        raise SystemExit(1)
    django.setup()


def resolve_ids_from_db(
    job_ref: str,
    rows: List[Dict[str, Any]],
    counting_id: int = DEFAULT_COUNTING_ID,
    counting_order: Optional[int] = None,
) -> Tuple[int, int, int, List[Dict[str, Any]]]:
    from apps.inventory.models import Assigment, Job
    from apps.masterdata.models import Location, Product
    from django.db.models import Q

    job = Job.objects.get(reference=job_ref)
    if counting_order is not None:
        assignment = (
            Assigment.objects.filter(job=job, counting__order=counting_order)
            .select_related("counting")
            .order_by("id")
            .first()
        )
        if not assignment:
            raise ValueError(
                f"Aucun assignment pour le job {job_ref} et counting__order={counting_order}"
            )
    else:
        assignment = (
            Assigment.objects.filter(job=job, counting_id=counting_id)
            .select_related("counting")
            .order_by("id")
            .first()
        )
        if not assignment:
            raise ValueError(
                f"Aucun assignment pour le job {job_ref} et counting_id={counting_id}"
            )

    counting_id = assignment.counting_id
    assignment_id = assignment.id
    job_id = job.id

    resolved_rows: List[Dict[str, Any]] = []
    for r in rows:
        loc = Location.objects.filter(
            Q(reference=r["location_ref"]) | Q(location_reference=r["location_ref"])
        ).first()
        if not loc:
            raise ValueError(f"Emplacement introuvable: {r['location_ref']}")

        bc = (r.get("barcode") or "").strip()
        product = (
            Product.objects.filter(Barcode__iexact=bc).first()
            or Product.objects.filter(Barcode=bc).first()
        )
        if not product:
            raise ValueError(f"Produit introuvable (code-barres): {bc}")

        entry: Dict[str, Any] = {
            "location_id": loc.id,
            "product_id": product.id,
            "quantity_inventoried": int(r["quantity"]),
        }
        if r.get("dlc") is not None and r.get("dlc") != "":
            entry["dlc"] = r["dlc"]
        if r.get("n_lot") is not None and r.get("n_lot") != "":
            entry["n_lot"] = r["n_lot"]
        resolved_rows.append(entry)

    return job_id, counting_id, assignment_id, resolved_rows


def preflight_job_detail_coverage(
    job_id: int,
    counting_id: int,
    rows_template: List[Dict[str, Any]],
    resolved_rows: List[Dict[str, Any]],
) -> List[str]:
    """
    Retourne la liste des références d'emplacement pour lesquelles il n'existe pas
    de JobDetail (job, counting, emplacement). Sans JobDetail, l'API mobile refuse la ligne
    (validation: \"JobDetail non trouvé...\").
    """
    from apps.inventory.models import JobDetail

    loc_ids = [r["location_id"] for r in resolved_rows]
    if not loc_ids:
        return []
    covered = set(
        JobDetail.objects.filter(
            job_id=job_id,
            counting_id=counting_id,
            location_id__in=loc_ids,
        ).values_list("location_id", flat=True)
    )
    missing_refs: List[str] = []
    for t, r in zip(rows_template, resolved_rows):
        if r["location_id"] not in covered:
            missing_refs.append(t.get("location_ref", str(r["location_id"])))
    return missing_refs


def preflight_dlc_n_lot(
    counting_id: int,
    rows_template: List[Dict[str, Any]],
    resolved_rows: List[Dict[str, Any]],
) -> List[str]:
    """Avertit si le mode de comptage / produit exige dlc ou n_lot non fournis dans les lignes."""
    from apps.inventory.models import Counting
    from apps.masterdata.models import Product

    issues: List[str] = []
    try:
        counting = Counting.objects.get(id=counting_id)
    except Counting.DoesNotExist:
        return [f"Comptage {counting_id} introuvable"]
    for i, (t, r) in enumerate(zip(rows_template, resolved_rows)):
        product = Product.objects.get(id=r["product_id"])
        if getattr(counting, "count_mode", None) == "par article":
            if counting.dlc and product.dlc and not t.get("dlc") and not r.get("dlc"):
                issues.append(
                    f"Ligne {i + 1} ({t.get('location_ref')}): champ 'dlc' obligatoire "
                    f"(comptage + produit exigent une DLC). Ajoutez 'dlc' dans DEFAULT_ROWS."
                )
            if counting.n_lot and product.n_lot and not t.get("n_lot") and not r.get("n_lot"):
                issues.append(
                    f"Ligne {i + 1} ({t.get('location_ref')}): champ 'n_lot' obligatoire. "
                    f"Ajoutez 'n_lot' dans DEFAULT_ROWS."
                )
    return issues


def filter_rows_with_job_detail(
    job_id: int,
    counting_id: int,
    rows_template: List[Dict[str, Any]],
    resolved_rows: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """
    Ne garde que les lignes pour lesquelles un JobDetail existe.
    Retourne (nouveau_template, nouvelles_lignes_résolues, nombre_ignoré).
    """
    from apps.inventory.models import JobDetail

    if not resolved_rows:
        return [], [], 0
    loc_ids = [r["location_id"] for r in resolved_rows]
    covered = set(
        JobDetail.objects.filter(
            job_id=job_id,
            counting_id=counting_id,
            location_id__in=loc_ids,
        ).values_list("location_id", flat=True)
    )
    new_t: List[Dict[str, Any]] = []
    new_r: List[Dict[str, Any]] = []
    for t, r in zip(rows_template, resolved_rows):
        if r["location_id"] in covered:
            new_t.append(t)
            new_r.append(r)
    skipped = len(rows_template) - len(new_t)
    return new_t, new_r, skipped


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


def post_counting_details(
    base_url: str,
    token: str,
    job_id: int,
    counting_id: int,
    assignment_id: int,
    rows: List[Dict[str, Any]],
) -> requests.Response:
    url = f"{base_url.rstrip('/')}/mobile/api/job/{job_id}/counting-detail/"
    payload: List[Dict[str, Any]] = []
    for row in rows:
        item: Dict[str, Any] = {
            "counting_id": counting_id,
            "location_id": row["location_id"],
            "quantity_inventoried": row["quantity_inventoried"],
            "assignment_id": assignment_id,
            "product_id": row["product_id"],
        }
        if row.get("dlc") is not None and row.get("dlc") != "":
            item["dlc"] = row["dlc"]
        if row.get("n_lot") is not None and row.get("n_lot") != "":
            item["n_lot"] = row["n_lot"]
        payload.append(item)
    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload),
        timeout=300,
    )
    return r


def main() -> int:
    parser = argparse.ArgumentParser(
        description="POST batch CountingDetail (API mobile)"
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="URL du serveur")
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--job-ref", default=DEFAULT_JOB_REF, help="Référence job (résolution DB)")
    parser.add_argument(
        "--counting-pk",
        type=int,
        default=DEFAULT_COUNTING_ID,
        dest="counting_pk",
        metavar="ID",
        help=f"ID du comptage (Counting.id) pour l'assignment en mode auto (défaut: {DEFAULT_COUNTING_ID})",
    )
    parser.add_argument(
        "--counting-order",
        type=int,
        default=None,
        metavar="N",
        help="Si défini, ignore --counting-pk et sélectionne l'assignment par ordre de comptage (1, 2, …).",
    )
    parser.add_argument(
        "--job-id",
        type=int,
        default=None,
        help="ID job (optionnel: sinon déduit de --job-ref)",
    )
    parser.add_argument(
        "--counting-id",
        type=int,
        default=None,
        help="ID counting (optionnel: sinon déduit de l'assignment)",
    )
    parser.add_argument(
        "--assignment-id",
        type=int,
        default=None,
        help="ID assignment (mode manuel; sinon déduit du job + counting_id / order)",
    )
    parser.add_argument(
        "--filter-covered",
        action="store_true",
        help="N'envoyer que les lignes pour lesquelles un JobDetail existe (job+comptage+emplacement).",
    )
    parser.add_argument(
        "--no-preflight",
        action="store_true",
        help="Ne pas vérifier JobDetail / dlc n_lot en local avant l'appel API.",
    )
    args = parser.parse_args()

    rows_template = [dict(r) for r in DEFAULT_ROWS]
    setup_django()

    # Toujours résoudre emplacements + produits depuis les références
    if args.job_id and args.counting_id and args.assignment_id:
        from apps.inventory.models import Job
        from apps.masterdata.models import Location, Product
        from django.db.models import Q

        job = Job.objects.get(id=args.job_id)
        if job.reference != args.job_ref:
            print(
                f"Avertissement: --job-id={args.job_id} pointe sur {job.reference!r}, "
                f"différent de --job-ref={args.job_ref!r} (résolution des lignes inchangée).",
                file=sys.stderr,
            )
        resolved_rows: List[Dict[str, Any]] = []
        for r in rows_template:
            loc = Location.objects.filter(
                Q(reference=r["location_ref"]) | Q(location_reference=r["location_ref"])
            ).first()
            if not loc:
                raise SystemExit(f"Emplacement introuvable: {r['location_ref']}")
            bc = (r.get("barcode") or "").strip()
            product = Product.objects.filter(Barcode__iexact=bc).first()
            if not product:
                raise SystemExit(f"Produit introuvable (code-barres): {bc}")
            entry = {
                "location_id": loc.id,
                "product_id": product.id,
                "quantity_inventoried": int(r["quantity"]),
            }
            if r.get("dlc") is not None and r.get("dlc") != "":
                entry["dlc"] = r["dlc"]
            if r.get("n_lot") is not None and r.get("n_lot") != "":
                entry["n_lot"] = r["n_lot"]
            resolved_rows.append(entry)
        job_id = args.job_id
        counting_id = args.counting_id
        assignment_id = args.assignment_id
    else:
        job_id, counting_id, assignment_id, resolved_rows = resolve_ids_from_db(
            args.job_ref,
            rows_template,
            counting_id=args.counting_pk,
            counting_order=args.counting_order,
        )

    if not args.no_preflight:
        dlc_issues = preflight_dlc_n_lot(counting_id, rows_template, resolved_rows)
        for msg in dlc_issues:
            print(f"[PREVOL] {msg}", file=sys.stderr)
        if dlc_issues:
            print(
                "\nCorrigez DEFAULT_ROWS (champs dlc / n_lot) ou utilisez --no-preflight "
                "pour tenter l'appel quand même.\n",
                file=sys.stderr,
            )
            raise SystemExit(1)

        missing = preflight_job_detail_coverage(
            job_id, counting_id, rows_template, resolved_rows
        )
        if missing:
            print(
                "\nAucun enregistrement possible tant qu'une ligne est invalide : l'API "
                "exige un **JobDetail** pour chaque couple (job, comptage, emplacement).\n"
                f"Emplacements sans JobDetail pour ce job/comptage : {', '.join(missing)}\n"
                "Créez les lignes d'emplacements sur le job (planning) ou lancez avec :\n"
                "  --filter-covered   → n'envoie que les emplacements déjà rattachés au job.\n",
                file=sys.stderr,
            )
            if args.filter_covered:
                rows_template, resolved_rows, skipped = filter_rows_with_job_detail(
                    job_id, counting_id, rows_template, resolved_rows
                )
                print(
                    f"Filtre --filter-covered : {skipped} ligne(s) ignorée(s), "
                    f"{len(resolved_rows)} ligne(s) à envoyer.",
                    file=sys.stderr,
                )
                if not resolved_rows:
                    print("Aucune ligne restante après filtrage.", file=sys.stderr)
                    raise SystemExit(1)
            else:
                raise SystemExit(1)

    print(
        f"Envoi: job_id={job_id}, counting_id={counting_id}, "
        f"assignment_id={assignment_id} ({len(resolved_rows)} lignes)"
    )
    token = login(args.base_url, args.username, args.password)
    r = post_counting_details(
        args.base_url, token, job_id, counting_id, assignment_id, resolved_rows
    )

    print("HTTP", r.status_code)
    try:
        body = r.json()
        print(json.dumps(body, indent=2, ensure_ascii=False))
        # success_response : { success, message, data: { success, total_processed, successful, ... } }
        data = body.get("data")
        if isinstance(data, dict) and "total_processed" in data:
            if not data.get("success", True):
                print(
                    "\nÉchec métier: success=False. Voir errors / message dans la réponse.",
                    file=sys.stderr,
                )
            elif data.get("successful", 0) < data.get("total_processed", 0):
                print(
                    "\n[ATTENTION] Traitement partiel : successful < total_processed.",
                    file=sys.stderr,
                )
    except Exception:
        print(r.text)

    if r.status_code in (200, 201):
        try:
            b = r.json()
            inner = b.get("data")
            if isinstance(inner, dict) and inner.get("success") is False:
                return 1
        except Exception:
            pass
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
