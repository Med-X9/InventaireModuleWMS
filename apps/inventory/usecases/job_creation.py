"""
Use case pour la création de jobs avec gestion des comptages multiples
"""
from typing import List, Dict, Any
from django.db import transaction
from django.utils import timezone
from ..models import Job, JobDetail, Assigment, Counting, Inventory, Warehouse, Location
from ..exceptions import JobCreationError
import logging

logger = logging.getLogger(__name__)

class JobCreationUseCase:
    """
    Use case pour la création de jobs avec gestion des comptages multiples
    """
    
    def __init__(self):
        pass
    
    def execute(self, inventory_id: int, warehouse_id: int, emplacement_ids: List[int]) -> Dict[str, Any]:
        """
        Crée des jobs pour un inventaire et un warehouse avec les emplacements spécifiés
        
        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt
            emplacement_ids: Liste des IDs des emplacements
            
        Returns:
            Dict[str, Any]: Résultat du traitement
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        try:
            with transaction.atomic():
                # Vérifier que l'inventaire existe
                inventory = Inventory.objects.get(id=inventory_id)
                
                # Vérifier que le warehouse existe
                warehouse = Warehouse.objects.get(id=warehouse_id)
                
                # Vérifier qu'il y a au moins deux comptages pour cet inventaire
                countings = Counting.objects.filter(inventory=inventory).order_by('order')
                if countings.count() < 2:
                    raise JobCreationError(f"Il faut au moins deux comptages pour l'inventaire {inventory.reference}. Comptages trouvés : {countings.count()}")
                
                # Prendre les deux premiers comptages
                counting1 = countings.filter(order=1).first()  # 1er comptage
                counting2 = countings.filter(order=2).first()  # 2ème comptage
                
                if not counting1 or not counting2:
                    raise JobCreationError(f"Comptages d'ordre 1 et 2 requis pour l'inventaire {inventory.reference}")
                
                # Vérifier que tous les emplacements existent et appartiennent au warehouse
                locations = []
                for emplacement_id in emplacement_ids:
                    location = Location.objects.get(id=emplacement_id)
                    
                    # Vérifier que l'emplacement appartient au warehouse
                    if location.sous_zone.zone.warehouse.id != warehouse_id:
                        raise JobCreationError(f"L'emplacement {location.location_reference} n'appartient pas au warehouse {warehouse.warehouse_name}")
                    
                    # Vérifier que l'emplacement n'est pas déjà affecté à un autre job pour cet inventaire
                    existing_job_detail = JobDetail.objects.filter(
                        location=location,
                        job__inventory=inventory
                    ).first()
                    
                    if existing_job_detail:
                        raise JobCreationError(f"L'emplacement {location.location_reference} est déjà affecté au job {existing_job_detail.job.reference}")
                    
                    locations.append(location)
                
                # Créer un seul job pour tous les emplacements
                job = Job.objects.create(
                    reference=Job().generate_reference(Job.REFERENCE_PREFIX),
                    status='EN ATTENTE',
                    en_attente_date=timezone.now(),
                    warehouse=warehouse,
                    inventory=inventory
                )
                
                # Créer les JobDetail selon la logique des comptages
                if counting1.count_mode == "image de stock":
                    # Cas 1: 1er comptage = image de stock
                    # Créer les emplacements seulement pour le 2ème comptage
                    logger.info(f"Configuration 'image de stock' détectée pour l'inventaire {inventory.reference}")
                    
                    for location in locations:
                        JobDetail.objects.create(
                            reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                            location=location,
                            job=job,
                            counting=counting2,  # Assigner au 2ème comptage
                            status='EN ATTENTE'
                        )
                    
                    # Créer seulement l'affectation pour le 2ème comptage
                    Assigment.objects.create(
                        reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                        job=job,
                        counting=counting2,
                        status='EN ATTENTE'
                    )
                    
                    logger.info(f"Job {job.reference} créé avec {len(locations)} emplacements pour le 2ème comptage uniquement")
                    
                else:
                    # Cas 2: 1er comptage différent de "image de stock"
                    # Dupliquer les emplacements pour les deux comptages
                    logger.info(f"Configuration normale détectée pour l'inventaire {inventory.reference}")
                    
                    for location in locations:
                        # Créer un JobDetail pour le 1er comptage
                        JobDetail.objects.create(
                            reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                            location=location,
                            job=job,
                            counting=counting1,
                            status='EN ATTENTE'
                        )
                        
                        # Créer un JobDetail pour le 2ème comptage
                        JobDetail.objects.create(
                            reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                            location=location,
                            job=job,
                            counting=counting2,
                            status='EN ATTENTE'
                        )
                    
                    # Créer les affectations pour les deux comptages
                    for counting in [counting1, counting2]:
                        Assigment.objects.create(
                            reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                            job=job,
                            counting=counting,
                            status='EN ATTENTE'
                        )
                    
                    logger.info(f"Job {job.reference} créé avec {len(locations) * 2} emplacements (dupliqués pour les deux comptages)")
                
                return {
                    'success': True,
                    'message': f'Job {job.reference} créé avec succès',
                    'job_id': job.id,
                    'job_reference': job.reference,
                    'emplacements_count': len(locations),
                    'counting1_mode': counting1.count_mode,
                    'counting2_mode': counting2.count_mode,
                    'assignments_created': Assigment.objects.filter(job=job).count()
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
            raise JobCreationError(f"Erreur inattendue lors de la création des jobs : {str(e)}")
