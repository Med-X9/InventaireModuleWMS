from ..models import Warehouse, Location, Zone
from ..exceptions import WarehouseNotFoundError
from apps.inventory.models import Job, JobDetail
import logging

logger = logging.getLogger(__name__)

class LocationService:
    @staticmethod
    def get_all_warehouse_locations(warehouse_id):
        """
        Récupère toutes les locations d'un warehouse via la relation warehouse -> zone -> location
        
        Args:
            warehouse_id: L'ID du warehouse
            
        Returns:
            dict: Dictionnaire contenant les données et un message d'information
        """
        try:
            logger.info(f"Récupération de toutes les locations pour le warehouse {warehouse_id}")
            
            # 1. Vérifier si le warehouse existe
            warehouse = Warehouse.objects.filter(id=warehouse_id).first()
            if not warehouse:
                logger.error(f"L'entrepôt avec l'ID {warehouse_id} n'existe pas")
                return {
                    'status': 'error',
                    'message': f"L'entrepôt avec l'ID {warehouse_id} n'existe pas",
                    'data': []
                }
            
            logger.info(f"Entrepôt trouvé: {warehouse.warehouse_name} (ID: {warehouse.id}, Status: {warehouse.status})")
            
            # 2. Vérifier les zones de l'entrepôt
            zones = Zone.objects.filter(warehouse=warehouse)
            logger.info(f"Nombre de zones trouvées: {zones.count()}")
            
            if not zones.exists():
                logger.error(f"L'entrepôt {warehouse.warehouse_name} n'a pas de zones")
                return {
                    'status': 'error',
                    'message': f"L'entrepôt {warehouse.warehouse_name} n'a pas de zones",
                    'data': []
                }
            
            # Log des détails des zones
            for zone in zones:
                logger.info(f"Zone trouvée: {zone.zone_name} (ID: {zone.id}, Status: {zone.zone_status})")
            
            # 3. Récupérer toutes les locations via les zones
            locations = Location.objects.filter(
                zone__in=zones,
                is_active=True  # Ne récupérer que les locations actives
            ).select_related('zone', 'location_type')
            
            logger.info(f"Nombre total de locations trouvées: {locations.count()}")
            
            if not locations.exists():
                logger.error(f"Aucune location active trouvée pour les zones de l'entrepôt {warehouse.warehouse_name}")
                return {
                    'status': 'error',
                    'message': f"Aucune location active trouvée pour les zones de l'entrepôt {warehouse.warehouse_name}",
                    'data': []
                }
            
            # Log des détails des locations
            for location in locations:
                logger.info(f"Location trouvée: {location.location_code} (ID: {location.id}, Zone: {location.zone.zone_name}, Type: {location.location_type.name if location.location_type else 'Non défini'})")
            
            logger.info(f"{locations.count()} locations trouvées pour l'entrepôt {warehouse.warehouse_name}")
            return {
                'status': 'success',
                'message': f"{locations.count()} locations trouvées pour l'entrepôt {warehouse.warehouse_name}",
                'data': locations
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des locations: {str(e)}")
            return {
                'status': 'error',
                'message': f"Une erreur est survenue lors de la récupération des locations: {str(e)}",
                'data': []
            }

    @staticmethod
    def get_warehouse_job_locations(warehouse_id):
        """
        Récupère toutes les locations groupées par job pour un warehouse
        
        Args:
            warehouse_id: L'ID du warehouse
            
        Returns:
            dict: Dictionnaire contenant les données et un message d'information
        """
        try:
            logger.info(f"Récupération des locations par job pour le warehouse {warehouse_id}")
            
            # 1. Vérifier si le warehouse existe
            warehouse = Warehouse.objects.filter(id=warehouse_id).first()
            if not warehouse:
                logger.error(f"L'entrepôt avec l'ID {warehouse_id} n'existe pas")
                return {
                    'status': 'error',
                    'message': f"L'entrepôt avec l'ID {warehouse_id} n'existe pas",
                    'data': []
                }
            
            logger.info(f"Entrepôt trouvé: {warehouse.warehouse_name}")
            
            # 2. Récupérer tous les jobs non supprimés pour ce warehouse
            jobs = Job.objects.filter(
                warehouse=warehouse,
                is_deleted=False
            ).prefetch_related('jobdetail_set__location')
            
            if not jobs.exists():
                logger.error(f"Aucun job trouvé pour l'entrepôt {warehouse.warehouse_name}")
                return {
                    'status': 'error',
                    'message': f"Aucun job trouvé pour l'entrepôt {warehouse.warehouse_name}",
                    'data': []
                }
            
            logger.info(f"Nombre de jobs trouvés: {jobs.count()}")
            
            # 3. Préparer les données
            jobs_data = []
            for job in jobs:
                # Récupérer les job details avec leurs locations
                job_details = JobDetail.objects.filter(
                    job=job,
                    is_deleted=False
                ).select_related('location', 'location__zone', 'location__location_type')
                
                logger.info(f"Job {job.reference}: {job_details.count()} locations trouvées")
                
                # Ajouter les données du job
                jobs_data.append({
                    'job_id': job.id,
                    'job_reference': job.reference,
                    'job_status': job.status,
                    'locations': [detail.location for detail in job_details]
                })
            
            return {
                'status': 'success',
                'message': f"{len(jobs_data)} jobs trouvés pour l'entrepôt {warehouse.warehouse_name}",
                'data': jobs_data
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des locations par job: {str(e)}")
            return {
                'status': 'error',
                'message': f"Une erreur est survenue lors de la récupération des locations par job: {str(e)}",
                'data': []
            } 