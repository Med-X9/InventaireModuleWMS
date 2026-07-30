"""
Service : clôture forcée de jobs sélectionnés (inventaire MAGASIN uniquement).

Pour chaque job :
- CountingDetail article barcode technique + quantité 0 sur chaque emplacement
- JobDetail → TERMINE
- Assignment (comptage 1) → TERMINE
- Job → TERMINE
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from apps.inventory.constants import InventoryType, StockGapGrouping
from apps.inventory.exceptions.job_exceptions import JobCreationError
from apps.inventory.models import Assigment, Counting, CountingDetail, Job, JobDetail
from apps.masterdata.models import Product

logger = logging.getLogger(__name__)


class MagasinJobsForceCompleteService:
    """
    Termine des jobs MAGASIN avec un article technique (barcode) et qté 0.
    Interdit pour GENERAL et TOURNANT.
    """

    DEFAULT_BARCODE = StockGapGrouping.FORCE_COMPLETE_BARCODE
    DEFAULT_QUANTITY = 0

    def force_complete(
        self,
        job_ids: List[int],
        barcode: Optional[str] = None,
        quantity: int = DEFAULT_QUANTITY,
    ) -> Dict[str, Any]:
        """
        Clôture forcée des jobs sélectionnés.

        Args:
            job_ids: IDs des jobs à terminer
            barcode: Barcode produit technique (défaut 11111111111)
            quantity: Quantité inventoriée (défaut 0)

        Returns:
            Dict avec statistiques et détail par job

        Raises:
            JobCreationError: Validation métier échouée
        """
        if not job_ids:
            raise JobCreationError("La liste job_ids ne peut pas être vide")

        barcode = (barcode or self.DEFAULT_BARCODE).strip()
        product = self._resolve_product(barcode)

        jobs = list(
            Job.objects.filter(id__in=job_ids)
            .select_related("inventory", "warehouse")
            .prefetch_related("jobdetail_set", "assigment_set")
        )
        found_ids = {job.id for job in jobs}
        missing = sorted(set(job_ids) - found_ids)
        if missing:
            raise JobCreationError(
                f"Jobs introuvables: {', '.join(map(str, missing))}"
            )

        non_magasin = [
            f"{job.reference} (type={job.inventory.inventory_type})"
            for job in jobs
            if job.inventory.inventory_type != InventoryType.MAGASIN
        ]
        if non_magasin:
            raise JobCreationError(
                "Cette API est réservée aux inventaires MAGASIN. "
                f"Jobs refusés: {', '.join(non_magasin)}"
            )

        results: List[Dict[str, Any]] = []
        with transaction.atomic():
            for job in jobs:
                results.append(
                    self._complete_one_job(job, product, quantity)
                )

        closed = sum(1 for r in results if r.get("job_closed"))
        return {
            "barcode": product.Barcode,
            "product_id": product.id,
            "quantity": quantity,
            "jobs_requested": len(job_ids),
            "jobs_closed": closed,
            "jobs": results,
        }

    def _resolve_product(self, barcode: str) -> Product:
        """Cherche le produit technique (barcode demandé puis fallbacks)."""
        candidates = [barcode]
        for fb in StockGapGrouping.FORCE_COMPLETE_BARCODE_FALLBACKS:
            if fb not in candidates:
                candidates.append(fb)

        for code in candidates:
            product = Product.objects.filter(Barcode=code).first()
            if product:
                return product

        raise JobCreationError(
            f"Produit technique introuvable pour barcode(s): "
            f"{', '.join(candidates)}. "
            f"Créez l'article avec Barcode={self.DEFAULT_BARCODE}."
        )

    def _complete_one_job(
        self,
        job: Job,
        product: Product,
        quantity: int,
    ) -> Dict[str, Any]:
        """Clôture un job MAGASIN (comptage 1 uniquement)."""
        now = timezone.now()
        detail: Dict[str, Any] = {
            "job_id": job.id,
            "reference": job.reference,
            "warehouse_id": job.warehouse_id,
            "inventory_id": job.inventory_id,
            "status_before": job.status,
            "job_closed": False,
            "job_details_closed": 0,
            "assignments_closed": 0,
            "counting_details_created": 0,
            "skipped": False,
            "message": "",
        }

        if job.status == "TERMINE":
            detail["skipped"] = True
            detail["message"] = "Job déjà TERMINE"
            return detail

        counting = Counting.objects.filter(
            inventory_id=job.inventory_id, order=1
        ).first()
        if not counting:
            raise JobCreationError(
                f"Comptage d'ordre 1 introuvable pour le job {job.reference}"
            )

        job_details = list(
            JobDetail.objects.filter(job=job, counting=counting).select_related(
                "location"
            )
        )
        if not job_details:
            # Fallback : JobDetails sans filtre counting (données hétérogènes)
            job_details = list(
                JobDetail.objects.filter(job=job).select_related("location")
            )
        if not job_details:
            raise JobCreationError(
                f"Aucun JobDetail pour le job {job.reference}"
            )

        # 1) CountingDetail qté 0 par emplacement unique
        location_ids = []
        seen_loc = set()
        for jd in job_details:
            if jd.location_id not in seen_loc:
                seen_loc.add(jd.location_id)
                location_ids.append(jd.location_id)

        existing = set(
            CountingDetail.objects.filter(
                job=job,
                counting=counting,
                product=product,
                location_id__in=location_ids,
            ).values_list("location_id", flat=True)
        )

        to_create: List[CountingDetail] = []
        for location_id in location_ids:
            if location_id in existing:
                continue
            cd = CountingDetail(
                quantity_inventoried=quantity,
                product=product,
                location_id=location_id,
                counting=counting,
                job=job,
            )
            cd.reference = cd.generate_reference(CountingDetail.REFERENCE_PREFIX)
            to_create.append(cd)

        if to_create:
            CountingDetail.objects.bulk_create(to_create)
            # Références avec IDs réels après insert
            for cd in to_create:
                if not cd.reference or cd.pk:
                    cd.reference = cd.generate_reference(
                        CountingDetail.REFERENCE_PREFIX
                    )
            CountingDetail.objects.bulk_update(to_create, ["reference"])
            detail["counting_details_created"] = len(to_create)

        # 2) JobDetails → TERMINE
        jd_updates = []
        for jd in job_details:
            if jd.status != "TERMINE":
                detail["job_details_closed"] += 1
            jd.status = "TERMINE"
            jd.termine_date = now
            jd_updates.append(jd)
        if jd_updates:
            JobDetail.objects.bulk_update(
                jd_updates, ["status", "termine_date"]
            )

        # 3) Assignments du comptage 1 (ou tous si mono-comptage)
        assignments = list(
            Assigment.objects.filter(job=job, counting=counting)
        )
        if not assignments:
            assignments = list(Assigment.objects.filter(job=job))

        for assignment in assignments:
            if assignment.status != "TERMINE":
                assignment.status = "TERMINE"
                assignment.termine_date = now
                assignment.save(
                    update_fields=["status", "termine_date", "updated_at"]
                )
                detail["assignments_closed"] += 1

        # 4) Job → TERMINE
        job.status = "TERMINE"
        job.termine_date = now
        job.termine_etat = "manuelle"
        job.termine_etat_date = now
        job.save(
            update_fields=[
                "status",
                "termine_date",
                "termine_etat",
                "termine_etat_date",
                "updated_at",
            ]
        )
        detail["job_closed"] = True
        detail["status_after"] = "TERMINE"
        detail["message"] = "Job clôturé avec article technique qté 0"

        logger.info(
            "Force-complete MAGASIN job=%s barcode=%s cd_created=%s",
            job.reference,
            product.Barcode,
            detail["counting_details_created"],
        )
        return detail
