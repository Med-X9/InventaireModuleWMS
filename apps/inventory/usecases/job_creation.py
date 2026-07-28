"""
Use case pour la création de jobs avec gestion des comptages
selon le type d'inventaire (GENERAL / MAGASIN / TOURNANT).
"""
from typing import List, Dict, Any
from django.db import transaction
from django.utils import timezone

from apps.inventory.constants import InventoryType, CountMode
from ..models import Job, JobDetail, Assigment, Counting, Inventory, Warehouse, Location
from ..exceptions import JobCreationError
import logging

logger = logging.getLogger(__name__)


class JobCreationUseCase:
    """
    Use case pour la création de jobs.

    - GENERAL : 2 comptages (JobDetail + Assigment dupliqués, sauf image de stock)
    - MAGASIN / TOURNANT : 1 seul comptage (ordre 1)
    """

    def execute(
        self, inventory_id: int, warehouse_id: int, emplacement_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Crée un job pour un inventaire et un warehouse avec les emplacements donnés.

        Raises:
            JobCreationError: Si une erreur métier survient
        """
        try:
            with transaction.atomic():
                inventory = Inventory.objects.get(id=inventory_id)
                warehouse = Warehouse.objects.get(id=warehouse_id)

                countings = Counting.objects.filter(inventory=inventory).order_by(
                    "order"
                )
                counting1 = countings.filter(order=1).first()
                counting2 = countings.filter(order=2).first()

                is_single_counting = (
                    inventory.inventory_type in InventoryType.SINGLE_COUNTING
                )

                if is_single_counting:
                    if not counting1:
                        raise JobCreationError(
                            f"Au moins un comptage (ordre 1) est requis pour "
                            f"l'inventaire {inventory.reference} "
                            f"(type {inventory.inventory_type}). "
                            f"Comptages trouvés : {countings.count()}"
                        )
                else:
                    # GENERAL (et types multi-comptages)
                    if countings.count() < 2 or not counting1 or not counting2:
                        raise JobCreationError(
                            f"Il faut au moins deux comptages pour l'inventaire "
                            f"{inventory.reference}. "
                            f"Comptages trouvés : {countings.count()}"
                        )

                locations = self._validate_locations(
                    emplacement_ids, warehouse_id, warehouse, inventory
                )

                job = Job.objects.create(
                    status="EN ATTENTE",
                    en_attente_date=timezone.now(),
                    warehouse=warehouse,
                    inventory=inventory,
                )

                if is_single_counting:
                    result = self._create_for_single_counting(
                        job, locations, counting1, inventory
                    )
                elif counting1.count_mode in (
                    CountMode.STOCK_IMAGE,
                    CountMode.STOCK_IMAGE_ALIAS,
                    "image de stock",
                ):
                    result = self._create_for_stock_image(
                        job, locations, counting2, inventory
                    )
                else:
                    result = self._create_for_dual_counting(
                        job, locations, counting1, counting2, inventory
                    )

                return {
                    "success": True,
                    "message": f"Job {job.reference} créé avec succès",
                    "job_id": job.id,
                    "job_reference": job.reference,
                    "inventory_type": inventory.inventory_type,
                    "emplacements_count": len(locations),
                    "counting1_mode": counting1.count_mode if counting1 else None,
                    "counting2_mode": counting2.count_mode if counting2 else None,
                    "assignments_created": Assigment.objects.filter(job=job).count(),
                    **result,
                }

        except Inventory.DoesNotExist:
            raise JobCreationError(f"Inventaire avec l'ID {inventory_id} non trouvé")
        except Warehouse.DoesNotExist:
            raise JobCreationError(f"Warehouse avec l'ID {warehouse_id} non trouvé")
        except Location.DoesNotExist as e:
            raise JobCreationError(f"Emplacement non trouvé: {str(e)}")
        except JobCreationError:
            raise
        except Exception as e:
            raise JobCreationError(
                f"Erreur inattendue lors de la création des jobs : {str(e)}"
            )

    def _validate_locations(
        self,
        emplacement_ids: List[int],
        warehouse_id: int,
        warehouse: Warehouse,
        inventory: Inventory,
    ) -> List[Location]:
        locations = []
        for emplacement_id in emplacement_ids:
            location = Location.objects.get(id=emplacement_id)

            if location.sous_zone.zone.warehouse.id != warehouse_id:
                raise JobCreationError(
                    f"L'emplacement {location.location_reference} n'appartient pas "
                    f"au warehouse {warehouse.warehouse_name}"
                )

            existing_job_detail = JobDetail.objects.filter(
                location=location,
                job__inventory=inventory,
            ).first()
            if existing_job_detail:
                raise JobCreationError(
                    f"L'emplacement {location.location_reference} est déjà affecté "
                    f"au job {existing_job_detail.job.reference}"
                )
            locations.append(location)
        return locations

    def _create_for_single_counting(
        self,
        job: Job,
        locations: List[Location],
        counting1: Counting,
        inventory: Inventory,
    ) -> Dict[str, Any]:
        """MAGASIN / TOURNANT : JobDetail + Assigment pour le comptage 1 uniquement."""
        logger.info(
            "Création job mono-comptage inventaire=%s type=%s",
            inventory.reference,
            inventory.inventory_type,
        )
        for location in locations:
            JobDetail.objects.create(
                reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                location=location,
                job=job,
                counting=counting1,
                status="EN ATTENTE",
            )

        Assigment.objects.create(
            reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
            job=job,
            counting=counting1,
            status="EN ATTENTE",
        )

        logger.info(
            "Job %s créé avec %s emplacements (comptage ordre 1)",
            job.reference,
            len(locations),
        )
        return {"mode": "single_counting", "job_details_count": len(locations)}

    def _create_for_stock_image(
        self,
        job: Job,
        locations: List[Location],
        counting2: Counting,
        inventory: Inventory,
    ) -> Dict[str, Any]:
        """GENERAL : 1er comptage image de stock → JobDetail/Assigment sur comptage 2."""
        logger.info(
            "Configuration image de stock pour inventaire %s", inventory.reference
        )
        for location in locations:
            JobDetail.objects.create(
                reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                location=location,
                job=job,
                counting=counting2,
                status="EN ATTENTE",
            )

        Assigment.objects.create(
            reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
            job=job,
            counting=counting2,
            status="EN ATTENTE",
        )
        return {"mode": "stock_image", "job_details_count": len(locations)}

    def _create_for_dual_counting(
        self,
        job: Job,
        locations: List[Location],
        counting1: Counting,
        counting2: Counting,
        inventory: Inventory,
    ) -> Dict[str, Any]:
        """GENERAL : JobDetail + Assigment pour les 2 comptages."""
        logger.info(
            "Configuration bi-comptage pour inventaire %s", inventory.reference
        )
        for location in locations:
            for counting in (counting1, counting2):
                JobDetail.objects.create(
                    reference=JobDetail().generate_reference(
                        JobDetail.REFERENCE_PREFIX
                    ),
                    location=location,
                    job=job,
                    counting=counting,
                    status="EN ATTENTE",
                )

        for counting in (counting1, counting2):
            Assigment.objects.create(
                reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                job=job,
                counting=counting,
                status="EN ATTENTE",
            )

        logger.info(
            "Job %s créé avec %s emplacements (x2 comptages)",
            job.reference,
            len(locations),
        )
        return {"mode": "dual_counting", "job_details_count": len(locations) * 2}
