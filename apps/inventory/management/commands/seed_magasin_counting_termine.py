"""
Insère des CountingDetail (API mobile / CountingDetailService) pour chaque magasin
d'un inventaire MAGASIN, avec articles mélangés, puis passe Job + Assigment en TERMINE.

Usage:
  python manage.py seed_magasin_counting_termine --inventory-id 24 --confirm
  python manage.py seed_magasin_counting_termine --confirm
"""
from __future__ import annotations

import random
from typing import Any, Dict, List

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.inventory.models import Assigment, EcartComptage, Job, JobDetail, Personne
from apps.inventory.services.ecart_stock_theorique_service import (
    EcartStockTheoriqueService,
)
from apps.masterdata.models import Stock
from apps.mobile.services.assignment_service import AssignmentService
from apps.mobile.services.counting_detail_service import CountingDetailService


class Command(BaseCommand):
    help = (
        "Insère des comptages (articles mélangés) pour tous les magasins "
        "puis passe jobs/assignments en TERMINE."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Obligatoire pour exécuter l'insertion.",
        )
        parser.add_argument(
            "--inventory-id",
            type=int,
            default=None,
            help="ID inventaire (défaut: dernier inventaire avec jobs).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Graine random pour quantités / mélange (défaut 42).",
        )
        parser.add_argument(
            "--sync-ecarts-stock",
            action="store_true",
            default=True,
            help="Synchronise EcartStockTheorique après insertion (défaut: oui).",
        )
        parser.add_argument(
            "--no-sync-ecarts-stock",
            action="store_false",
            dest="sync_ecarts_stock",
            help="Ne pas synchroniser EcartStockTheorique.",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError("Ajoutez --confirm pour insérer les comptages.")

        random.seed(options["seed"])
        inventory_id = options["inventory_id"]

        jobs = (
            Job.objects.filter(inventory_id=inventory_id)
            if inventory_id
            else Job.objects.filter(inventory__isnull=False).order_by("-inventory_id")
        )
        if not inventory_id:
            first = jobs.first()
            if not first:
                raise CommandError("Aucun job trouvé.")
            inventory_id = first.inventory_id
            jobs = Job.objects.filter(inventory_id=inventory_id)

        jobs = (
            jobs.select_related("warehouse", "inventory")
            .order_by("warehouse__warehouse_name", "id")
        )
        if not jobs.exists():
            raise CommandError(f"Aucun job pour inventaire {inventory_id}.")

        personne = Personne.objects.order_by("id").first()
        if not personne:
            raise CommandError("Aucune Personne en base (requise pour close_job).")

        counting_svc = CountingDetailService()
        assignment_svc = AssignmentService()
        ecart_stock_svc = EcartStockTheoriqueService()

        self.stdout.write(
            self.style.NOTICE(
                f"Inventaire {inventory_id} — {jobs.count()} jobs — "
                f"personne close=#{personne.id}"
            )
        )

        created_total = 0
        termine_jobs = 0
        errors: List[str] = []
        warehouse_ids: set[int] = set()

        for job in jobs:
            try:
                n = self._process_job(
                    job=job,
                    counting_svc=counting_svc,
                    assignment_svc=assignment_svc,
                    personne_id=personne.id,
                )
                created_total += n
                termine_jobs += 1
                warehouse_ids.add(job.warehouse_id)
                wh_label = getattr(job.warehouse, "warehouse_name", None) or job.warehouse_id
                self.stdout.write(
                    f"  OK job={job.id} magasin={wh_label} lignes={n} → TERMINE"
                )
            except Exception as exc:  # noqa: BLE001 — seed: log et continue
                msg = f"job={job.id} wh={job.warehouse_id}: {exc}"
                errors.append(msg)
                self.stdout.write(self.style.ERROR(f"  ERR {msg}"))

        null_final = EcartComptage.objects.filter(
            inventory_id=inventory_id,
            final_result__isnull=True,
        ).count()
        if null_final:
            self.stdout.write(
                self.style.WARNING(
                    f"  Attention: {null_final} EcartComptage sans final_result "
                    f"(vérifiez inventory_type / Strategy)."
                )
            )

        if options["sync_ecarts_stock"] and warehouse_ids:
            self.stdout.write("Synchronisation EcartStockTheorique…")
            for wid in sorted(warehouse_ids):
                sync = ecart_stock_svc.sync_from_compute(
                    inventory_id, wid, only_nonzero=False
                )
                self.stdout.write(
                    f"  sync wh={wid}: créés={sync['created']} "
                    f"maj={sync['updated']} lignes={sync['total_compute_lines']}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Terminé: {created_total} lignes comptage, "
                f"{termine_jobs}/{jobs.count()} jobs TERMINE."
            )
        )
        if errors:
            self.stdout.write(self.style.WARNING(f"{len(errors)} erreur(s)."))
            for e in errors:
                self.stdout.write(f"  - {e}")
            raise CommandError("Certaines insertions ont échoué.")

    def _process_job(
        self,
        *,
        job: Job,
        counting_svc: CountingDetailService,
        assignment_svc: AssignmentService,
        personne_id: int,
    ) -> int:
        assignment = (
            Assigment.objects.filter(job=job)
            .select_related("counting")
            .order_by("id")
            .first()
        )
        if not assignment or not assignment.counting_id:
            raise CommandError(f"Pas d'assignment/counting pour job {job.id}")

        counting = assignment.counting
        job_details = list(
            JobDetail.objects.filter(job=job, counting=counting).select_related(
                "location"
            )
        )
        if not job_details:
            raise CommandError(f"Pas de JobDetail pour job {job.id}")

        stocks = list(
            Stock.objects.filter(
                inventory_id=job.inventory_id,
                warehouse_id=job.warehouse_id,
                product__isnull=False,
            ).select_related("product")
        )
        if not stocks:
            raise CommandError(
                f"Pas de stock pour magasin {job.warehouse_id} / inv {job.inventory_id}"
            )

        # Mélanger articles + emplacements pour des associations croisées
        random.shuffle(stocks)
        locations = [jd.location for jd in job_details if jd.location_id]
        random.shuffle(locations)
        if not locations:
            raise CommandError(f"Job {job.id}: JobDetails sans emplacement")

        payload: List[Dict[str, Any]] = []
        # Couvrir chaque emplacement + répartir tous les articles stock (cycle emplacements)
        product_ids_used = set()
        for idx, stock in enumerate(stocks):
            location = locations[idx % len(locations)]
            product_ids_used.add(stock.product_id)
            theo = int(stock.quantity_available or 0)
            # Quantités mélangées : égalité / écart + / écart -
            mode = idx % 3
            if mode == 0:
                qty = max(theo, 1)
            elif mode == 1:
                qty = max(theo + random.randint(1, 5), 1)
            else:
                qty = max(theo - random.randint(0, 3), 1)
            payload.append(
                {
                    "counting_id": counting.id,
                    "location_id": location.id,
                    "quantity_inventoried": qty,
                    "assignment_id": assignment.id,
                    "product_id": stock.product_id,
                }
            )

        # Garantir au moins 1 ligne par JobDetail (emplacements sans article assigné)
        covered_locs = {p["location_id"] for p in payload}
        spare_products = [s.product_id for s in stocks]
        for jd in job_details:
            if jd.location_id and jd.location_id not in covered_locs:
                pid = spare_products[len(payload) % len(spare_products)]
                payload.append(
                    {
                        "counting_id": counting.id,
                        "location_id": jd.location_id,
                        "quantity_inventoried": random.randint(1, 10),
                        "assignment_id": assignment.id,
                        "product_id": pid,
                    }
                )
                covered_locs.add(jd.location_id)

        result = counting_svc.create_counting_details_batch(payload, job_id=job.id)
        if not result.get("success"):
            raise CommandError(f"CountingDetail batch échoué: {result}")

        n_ok = len(result.get("results") or [])
        self._mark_termine(
            job=job,
            assignment=assignment,
            assignment_svc=assignment_svc,
            personne_id=personne_id,
        )
        return n_ok

    def _mark_termine(
        self,
        *,
        job: Job,
        assignment: Assigment,
        assignment_svc: AssignmentService,
        personne_id: int,
    ) -> None:
        """Passe assignment puis job en TERMINE (close_job ou force seed)."""
        now = timezone.now()

        # Passage réaliste vers un statut closable
        if assignment.status in ("PRET", "AFFECTE", "EN ATTENTE"):
            assignment.status = "ENTAME"
            assignment.entame_date = now
            assignment.save(update_fields=["status", "entame_date", "updated_at"])
        if job.status in ("PRET", "AFFECTE", "EN ATTENTE", "VALIDE"):
            job.status = "ENTAME"
            job.save(update_fields=["status", "updated_at"])

        try:
            assignment_svc.close_job(
                job_id=job.id,
                assignment_id=assignment.id,
                personnes_ids=[personne_id],
                user_id=None,
            )
        except Exception:
            # Seed: forcer TERMINE si close_job bloqué (écarts, transitions…)
            with transaction.atomic():
                Assigment.objects.filter(id=assignment.id).update(
                    status="TERMINE",
                    termine_date=now,
                    personne_id=personne_id,
                )
                Job.objects.filter(id=job.id).update(
                    status="TERMINE",
                    termine_date=now,
                )
                JobDetail.objects.filter(job=job, counting=assignment.counting).exclude(
                    status="TERMINE"
                ).update(status="TERMINE", termine_date=now)

        job.refresh_from_db()
        assignment.refresh_from_db()
        if assignment.status != "TERMINE":
            Assigment.objects.filter(id=assignment.id).update(
                status="TERMINE", termine_date=now
            )
        if job.status != "TERMINE":
            Job.objects.filter(id=job.id).update(status="TERMINE", termine_date=now)
