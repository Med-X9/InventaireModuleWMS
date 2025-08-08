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
                
                # Récupérer les comptages de l'inventaire
                countings = Counting.objects.filter(inventory=job.inventory).order_by('order')
                if countings.count() < 2:
                    raise JobCreationError(f"Il faut au moins deux comptages pour l'inventaire {job.inventory.reference}. Comptages trouvés : {countings.count()}")
                
                # Prendre les deux premiers comptages
                counting1 = countings.filter(order=1).first()  # 1er comptage
                counting2 = countings.filter(order=2).first()  # 2ème comptage
                
                if not counting1 or not counting2:
                    raise JobCreationError(f"Comptages d'ordre 1 et 2 requis pour l'inventaire {job.inventory.reference}")
                
                # Créer les JobDetail selon la logique des comptages
                created_count = 0
                
                if counting1.count_mode == "image de stock":
                    # Cas 1: 1er comptage = image de stock
                    # Créer les emplacements seulement pour le 2ème comptage
                    logger.info(f"Configuration 'image de stock' détectée pour l'inventaire {job.inventory.reference}")
                    
                    for location in locations:
                        # Vérifier si l'emplacement n'est pas déjà dans le job pour le 2ème comptage
                        existing_job_detail = JobDetail.objects.filter(
                            job=job,
                            location=location,
                            counting=counting2
                        ).first()
                        
                        if not existing_job_detail:
                            JobDetail.objects.create(
                                reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                                location=location,
                                job=job,
                                counting=counting2,  # Assigner au 2ème comptage
                                status='EN ATTENTE'
                            )
                            created_count += 1
                    
                    # Vérifier si une affectation existe déjà pour le 2ème comptage
                    existing_assignment = Assigment.objects.filter(
                        job=job,
                        counting=counting2
                    ).first()
                    
                    if not existing_assignment:
                        # Créer l'affectation pour le 2ème comptage si elle n'existe pas
                        Assigment.objects.create(
                            reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                            job=job,
                            counting=counting2,
                            status='EN ATTENTE'
                        )
                        logger.info(f"Affectation créée pour le 2ème comptage du job {job.reference}")
                    
                    logger.info(f"{created_count} emplacements ajoutés au job {job.reference} pour le 2ème comptage uniquement")
                    
                else:
                    # Cas 2: 1er comptage différent de "image de stock"
                    # Dupliquer les emplacements pour les deux comptages
                    logger.info(f"Configuration normale détectée pour l'inventaire {job.inventory.reference}")
                    
                    for location in locations:
                        # Vérifier si l'emplacement n'est pas déjà dans le job pour le 1er comptage
                        existing_job_detail_1 = JobDetail.objects.filter(
                            job=job,
                            location=location,
                            counting=counting1
                        ).first()
                        
                        if not existing_job_detail_1:
                            JobDetail.objects.create(
                                reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                                location=location,
                                job=job,
                                counting=counting1,
                                status='EN ATTENTE'
                            )
                            created_count += 1
                        
                        # Vérifier si l'emplacement n'est pas déjà dans le job pour le 2ème comptage
                        existing_job_detail_2 = JobDetail.objects.filter(
                            job=job,
                            location=location,
                            counting=counting2
                        ).first()
                        
                        if not existing_job_detail_2:
                            JobDetail.objects.create(
                                reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                                location=location,
                                job=job,
                                counting=counting2,
                                status='EN ATTENTE'
                            )
                            created_count += 1
                    
                    # Vérifier et créer les affectations si nécessaire
                    for counting in [counting1, counting2]:
                        existing_assignment = Assigment.objects.filter(
                            job=job,
                            counting=counting
                        ).first()
                        
                        if not existing_assignment:
                            Assigment.objects.create(
                                reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                                job=job,
                                counting=counting,
                                status='EN ATTENTE'
                            )
                            logger.info(f"Affectation créée pour le comptage {counting.order} du job {job.reference}")
                    
                    logger.info(f"{created_count} emplacements ajoutés au job {job.reference} (dupliqués pour les deux comptages)")
                
                return {
                    'success': True,
                    'message': f"{created_count} emplacements ajoutés au job {job.reference}",
                    'job_id': job_id,
                    'job_reference': job.reference,
                    'emplacements_added': created_count,
                    'counting1_mode': counting1.count_mode,
                    'counting2_mode': counting2.count_mode,
                    'assignments_count': Assigment.objects.filter(job=job).count()
                }
                
        except Job.DoesNotExist:
            raise JobCreationError(f"Job avec l'ID {job_id} non trouvé")
        except Location.DoesNotExist as e:
            raise JobCreationError(f"Emplacement non trouvé: {str(e)}")
        except JobCreationError:
            raise
        except Exception as e:
            raise JobCreationError(f"Erreur inattendue lors de l'ajout des emplacements : {str(e)}")
