"""
Use case pour l'ajout d'emplacements à un job avec gestion des comptages multiples
"""
from typing import List, Dict, Any
from django.db import transaction
from django.utils import timezone
from ..models import Job, JobDetail, Assigment, Counting, Location
from ..exceptions import JobCreationError
import logging

logger = logging.getLogger(__name__)

class JobAddEmplacementsUseCase:
    """
    Use case pour l'ajout d'emplacements à un job avec gestion des comptages multiples
    """
    
    def __init__(self):
        pass
    
    def execute(self, job_id: int, emplacement_ids: List[int]) -> Dict[str, Any]:
        """
        Ajoute des emplacements à un job existant avec gestion des comptages multiples
        
        Args:
            job_id: ID du job
            emplacement_ids: Liste des IDs des emplacements à ajouter
            
        Returns:
            Dict[str, Any]: Résultat du traitement
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        try:
            with transaction.atomic():
                # Vérifier que le job existe
                job = Job.objects.get(id=job_id)
                
                # Vérifier que tous les emplacements existent
                locations = []
                for emplacement_id in emplacement_ids:
                    location = Location.objects.get(id=emplacement_id)
                    
                    # Vérifier que l'emplacement n'est pas déjà affecté à un autre job pour cet inventaire
                    existing_job_detail = JobDetail.objects.filter(
                        location=location,
                        job__inventory=job.inventory
                    ).exclude(job=job).first()
                    
                    if existing_job_detail:
                        raise JobCreationError(f"L'emplacement {location.location_reference} est déjà affecté au job {existing_job_detail.job.reference}")
                    
                    locations.append(location)
                
                # Récupérer les comptages selon le type d'inventaire
                from apps.inventory.constants import InventoryType, CountMode

                countings = Counting.objects.filter(inventory=job.inventory).order_by(
                    "order"
                )
                counting1 = countings.filter(order=1).first()
                counting2 = countings.filter(order=2).first()
                is_single = job.inventory.inventory_type in InventoryType.SINGLE_COUNTING

                if is_single:
                    if not counting1:
                        raise JobCreationError(
                            f"Au moins un comptage (ordre 1) est requis pour "
                            f"l'inventaire {job.inventory.reference} "
                            f"(type {job.inventory.inventory_type}). "
                            f"Comptages trouvés : {countings.count()}"
                        )
                elif countings.count() < 2 or not counting1 or not counting2:
                    raise JobCreationError(
                        f"Il faut au moins deux comptages pour l'inventaire "
                        f"{job.inventory.reference}. "
                        f"Comptages trouvés : {countings.count()}"
                    )

                # Créer les JobDetail selon la logique des comptages
                created_count = 0

                if is_single:
                    target_countings = [counting1]
                    logger.info(
                        "Ajout emplacements mono-comptage inventaire=%s",
                        job.inventory.reference,
                    )
                elif counting1.count_mode in (
                    CountMode.STOCK_IMAGE,
                    CountMode.STOCK_IMAGE_ALIAS,
                    "image de stock",
                ):
                    target_countings = [counting2]
                    logger.info(
                        "Configuration image de stock pour inventaire %s",
                        job.inventory.reference,
                    )
                else:
                    target_countings = [counting1, counting2]
                    logger.info(
                        "Configuration bi-comptage pour inventaire %s",
                        job.inventory.reference,
                    )

                for location in locations:
                    for counting in target_countings:
                        existing_job_detail = JobDetail.objects.filter(
                            job=job,
                            location=location,
                            counting=counting,
                        ).first()
                        if not existing_job_detail:
                            JobDetail.objects.create(
                                reference=JobDetail().generate_reference(
                                    JobDetail.REFERENCE_PREFIX
                                ),
                                location=location,
                                job=job,
                                counting=counting,
                                status="EN ATTENTE",
                            )
                            created_count += 1

                for counting in target_countings:
                    existing_assignment = Assigment.objects.filter(
                        job=job,
                        counting=counting,
                    ).first()
                    if not existing_assignment:
                        Assigment.objects.create(
                            reference=Assigment().generate_reference(
                                Assigment.REFERENCE_PREFIX
                            ),
                            job=job,
                            counting=counting,
                            status="EN ATTENTE",
                        )
                        logger.info(
                            "Affectation créée pour le comptage %s du job %s",
                            counting.order,
                            job.reference,
                        )

                logger.info(
                    "%s emplacements ajoutés au job %s",
                    created_count,
                    job.reference,
                )

                return {
                    "success": True,
                    "message": f"{created_count} emplacements ajoutés au job {job.reference}",
                    "job_id": job_id,
                    "job_reference": job.reference,
                    "emplacements_added": created_count,
                    "inventory_type": job.inventory.inventory_type,
                    "counting1_mode": counting1.count_mode if counting1 else None,
                    "counting2_mode": counting2.count_mode if counting2 else None,
                    "assignments_count": Assigment.objects.filter(job=job).count(),
                }
                
        except Job.DoesNotExist:
            raise JobCreationError(f"Job avec l'ID {job_id} non trouvé")
        except Location.DoesNotExist as e:
            raise JobCreationError(f"Emplacement non trouvé: {str(e)}")
        except JobCreationError:
            raise
        except Exception as e:
            raise JobCreationError(f"Erreur inattendue lors de l'ajout des emplacements : {str(e)}")
