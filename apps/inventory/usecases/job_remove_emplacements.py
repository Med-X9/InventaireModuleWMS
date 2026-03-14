"""
Use case pour la suppression d'emplacements d'un job avec gestion des comptages multiples
"""
from typing import List, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from ..models import Job, JobDetail, Assigment, Counting, Location
from ..exceptions import JobCreationError
import logging

logger = logging.getLogger(__name__)

class JobRemoveEmplacementsUseCase:
    """
    Use case pour la suppression d'emplacements d'un job avec gestion des comptages multiples
    """
    
    def __init__(self):
        pass
    
    def execute(self, job_id: int, emplacement_ids: List[int]) -> Dict[str, Any]:
        """
        Supprime des emplacements d'un job existant avec gestion des comptages multiples
        
        Args:
            job_id: ID du job
            emplacement_ids: Liste des IDs des emplacements à supprimer
            
        Returns:
            Dict[str, Any]: Résultat du traitement
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        # Validation des paramètres d'entrée
        if not job_id or job_id <= 0:
            raise JobCreationError("ID de job invalide")
        
        if not emplacement_ids or len(emplacement_ids) == 0:
            raise JobCreationError("Liste d'emplacements vide")
        
        if not isinstance(emplacement_ids, list):
            raise JobCreationError("emplacement_ids doit être une liste")
        
        # Validation des IDs d'emplacements
        invalid_ids = [id for id in emplacement_ids if not isinstance(id, int) or id <= 0]
        if invalid_ids:
            raise JobCreationError(f"IDs d'emplacements invalides: {invalid_ids}")
        
        try:
            with transaction.atomic():
                # Vérifier que le job existe
                try:
                    job = Job.objects.get(id=job_id)
                except Job.DoesNotExist:
                    raise JobCreationError(f"Job avec l'ID {job_id} non trouvé")
                
                # Vérifier que tous les emplacements existent
                locations = []
                missing_locations = []
                
                for emplacement_id in emplacement_ids:
                    try:
                        location = Location.objects.get(id=emplacement_id)
                        locations.append(location)
                    except Location.DoesNotExist:
                        missing_locations.append(emplacement_id)
                
                if missing_locations:
                    raise JobCreationError(f"Emplacements non trouvés: {missing_locations}")
                
                # Vérifier que le job a des emplacements à supprimer
                existing_job_details = JobDetail.objects.filter(
                    job=job,
                    location__in=locations
                )
                
                if existing_job_details.count() == 0:
                    raise JobCreationError(f"Aucun emplacement à supprimer trouvé dans le job {job.reference}")
                
                # Récupérer les comptages de l'inventaire
                try:
                    countings = Counting.objects.filter(inventory=job.inventory).order_by('order')
                    if countings.count() < 2:
                        raise JobCreationError(
                            f"Il faut au moins deux comptages pour l'inventaire {job.inventory.reference}. "
                            f"Comptages trouvés : {countings.count()}"
                        )
                    
                    # Prendre les deux premiers comptages
                    counting1 = countings.filter(order=1).first()  # 1er comptage
                    counting2 = countings.filter(order=2).first()  # 2ème comptage
                    
                    if not counting1:
                        raise JobCreationError(f"Comptage d'ordre 1 manquant pour l'inventaire {job.inventory.reference}")
                    
                    if not counting2:
                        raise JobCreationError(f"Comptage d'ordre 2 manquant pour l'inventaire {job.inventory.reference}")
                        
                except Exception as e:
                    if isinstance(e, JobCreationError):
                        raise
                    raise JobCreationError(f"Erreur lors de la récupération des comptages: {str(e)}")
                
                # Supprimer les JobDetail selon la logique des comptages
                deleted_count = 0
                assignments_deleted = 0
                
                try:
                    if counting1.count_mode == "image de stock":
                        # Cas 1: 1er comptage = image de stock
                        # Supprimer les emplacements seulement pour le 2ème comptage
                        logger.info(f"Configuration 'image de stock' détectée pour l'inventaire {job.inventory.reference}")
                        
                        for location in locations:
                            # Supprimer les JobDetails pour le 2ème comptage uniquement
                            job_details_to_delete = JobDetail.objects.filter(
                                job=job,
                                location=location,
                                counting=counting2
                            )
                            
                            deleted_count += job_details_to_delete.count()
                            job_details_to_delete.delete()
                        
                        # Vérifier s'il reste des JobDetails pour le 2ème comptage
                        remaining_job_details = JobDetail.objects.filter(
                            job=job,
                            counting=counting2
                        ).count()
                        
                        # Si plus aucun JobDetail pour le 2ème comptage, supprimer l'affectation
                        if remaining_job_details == 0:
                            deleted_assignments = Assigment.objects.filter(
                                job=job,
                                counting=counting2
                            )
                            assignments_deleted = deleted_assignments.count()
                            deleted_assignments.delete()
                            logger.info(f"Affectation supprimée pour le 2ème comptage du job {job.reference}")
                        
                        logger.info(f"{deleted_count} emplacements supprimés du job {job.reference} pour le 2ème comptage uniquement")
                        
                    else:
                        # Cas 2: 1er comptage différent de "image de stock"
                        # Supprimer les emplacements pour les deux comptages
                        logger.info(f"Configuration normale détectée pour l'inventaire {job.inventory.reference}")
                        
                        for location in locations:
                            # Supprimer les JobDetails pour le 1er comptage
                            job_details_1 = JobDetail.objects.filter(
                                job=job,
                                location=location,
                                counting=counting1
                            )
                            deleted_count += job_details_1.count()
                            job_details_1.delete()
                            
                            # Supprimer les JobDetails pour le 2ème comptage
                            job_details_2 = JobDetail.objects.filter(
                                job=job,
                                location=location,
                                counting=counting2
                            )
                            deleted_count += job_details_2.count()
                            job_details_2.delete()
                        
                        # Vérifier s'il reste des JobDetails pour chaque comptage
                        remaining_job_details_1 = JobDetail.objects.filter(
                            job=job,
                            counting=counting1
                        ).count()
                        
                        remaining_job_details_2 = JobDetail.objects.filter(
                            job=job,
                            counting=counting2
                        ).count()
                        
                        # Si plus aucun JobDetail pour un comptage, supprimer l'affectation correspondante
                        if remaining_job_details_1 == 0:
                            deleted_assignments_1 = Assigment.objects.filter(
                                job=job,
                                counting=counting1
                            )
                            assignments_deleted += deleted_assignments_1.count()
                            deleted_assignments_1.delete()
                            logger.info(f"Affectation supprimée pour le 1er comptage du job {job.reference}")
                        
                        if remaining_job_details_2 == 0:
                            deleted_assignments_2 = Assigment.objects.filter(
                                job=job,
                                counting=counting2
                            )
                            assignments_deleted += deleted_assignments_2.count()
                            deleted_assignments_2.delete()
                            logger.info(f"Affectation supprimée pour le 2ème comptage du job {job.reference}")
                        
                        logger.info(f"{deleted_count} emplacements supprimés du job {job.reference} (pour les deux comptages)")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la suppression des JobDetails: {str(e)}")
                    raise JobCreationError(f"Erreur lors de la suppression des emplacements: {str(e)}")
                
                # Vérifier que la suppression a été effectuée
                if deleted_count == 0:
                    raise JobCreationError(f"Aucun emplacement supprimé du job {job.reference}")
                
                return {
                    'success': True,
                    'message': f"{deleted_count} emplacements supprimés du job {job.reference}",
                    'job_id': job_id,
                    'job_reference': job.reference,
                    'emplacements_deleted': deleted_count,
                    'assignments_deleted': assignments_deleted,
                    'counting1_mode': counting1.count_mode,
                    'counting2_mode': counting2.count_mode,
                    'assignments_count': Assigment.objects.filter(job=job).count()
                }
                
        except JobCreationError:
            # Re-raise les JobCreationError sans modification
            raise
        except ValidationError as e:
            # Convertir les ValidationError en JobCreationError
            raise JobCreationError(f"Erreur de validation: {str(e)}")
        except Exception as e:
            # Logger l'erreur pour le debugging
            logger.error(f"Erreur inattendue dans JobRemoveEmplacementsUseCase: {str(e)}")
            raise JobCreationError(f"Erreur inattendue lors de la suppression des emplacements: {str(e)}")
