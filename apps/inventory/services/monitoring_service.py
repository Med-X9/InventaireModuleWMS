"""
Service pour le monitoring par zone
"""
import logging
from typing import Dict, Any, List
from ..repositories.job_repository import JobRepository
from ..models import Job, Assigment, Counting
from ..exceptions.job_exceptions import JobCreationError

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Service pour calculer les statistiques de monitoring par zone
    Contient la logique métier pour le monitoring
    """
    
    def __init__(self):
        self.repository = JobRepository()
    
    def get_zone_monitoring_by_inventory_and_warehouse(
        self,
        inventory_id: int,
        warehouse_id: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère les statistiques de monitoring par zone pour un inventaire et un entrepôt.
        
        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt
            
        Returns:
            Liste des statistiques par zone avec les comptages
            
        Raises:
            JobCreationError: Si une erreur survient
        """
        try:
            # Récupérer les données depuis le repository
            data = self.repository.get_zone_stats_data(inventory_id, warehouse_id)
            zones = data['zones']
            jobs = data['jobs']
            countings = data['countings']
            
            # Vérifier que l'inventaire et l'entrepôt existent
            if not jobs:
                # Vérifier si l'inventaire et l'entrepôt existent
                inventory = self.repository.get_inventory_by_id(inventory_id)
                warehouse = self.repository.get_warehouse_by_id(warehouse_id)
                if not inventory:
                    raise JobCreationError(f"Inventaire avec l'ID {inventory_id} non trouvé")
                if not warehouse:
                    raise JobCreationError(f"Entrepôt avec l'ID {warehouse_id} non trouvé")
            
            # Construire les statistiques par zone
            zone_stats = []
            
            for zone in zones:
                # Filtrer les jobs qui appartiennent à cette zone
                zone_jobs = []
                seen_job_ids = set()
                for job in jobs:
                    # Vérifier si le job a au moins un JobDetail dans cette zone
                    for job_detail in job.jobdetail_set.all():
                        if job_detail.location.sous_zone.zone.id == zone.id:
                            if job.id not in seen_job_ids:
                                zone_jobs.append(job)
                                seen_job_ids.add(job.id)
                            break
                
                # Compter le nombre de jobs uniques dans cette zone
                unique_jobs = zone_jobs
                jobs_count = len(unique_jobs)
                
                # Compter le nombre d'équipes distinctes dans cette zone
                # Une équipe est identifiée par une combinaison unique de personne et personne_two
                # ou par session si elle existe
                teams = set()
                for job in unique_jobs:
                    for assignment in job.assigment_set.all():
                        # Identifier l'équipe par session si disponible
                        if assignment.session:
                            teams.add(assignment.session.id)
                        # Sinon, identifier par personne et personne_two
                        elif assignment.personne or assignment.personne_two:
                            team_key = (
                                assignment.personne_id if assignment.personne else None,
                                assignment.personne_two_id if assignment.personne_two else None
                            )
                            teams.add(team_key)
                
                teams_count = len(teams)
                
                # Calculer le statut de la zone basé sur les assignments
                zone_status = self._calculate_zone_status(unique_jobs)
                
                # Calculer les statistiques par comptage
                counting_stats = []
                for counting in countings:
                    # Filtrer les jobs de cette zone qui ont un assignment pour ce comptage
                    counting_jobs = []
                    for job in unique_jobs:
                        # Vérifier si le job a un assignment pour ce comptage
                        has_assignment = any(
                            a.counting_id == counting.id 
                            for a in job.assigment_set.all()
                        )
                        if has_assignment:
                            counting_jobs.append(job)
                    
                    total_jobs = len(counting_jobs)
                    
                    # Compter les jobs par statut
                    jobs_en_attente = sum(
                        1 for job in counting_jobs 
                        if job.status == 'TRANSFERT'
                    )
                    jobs_en_cours = sum(
                        1 for job in counting_jobs 
                        if job.status == 'ENTAME'
                    )
                    jobs_termines = sum(
                        1 for job in counting_jobs 
                        if job.status == 'TERMINE'
                    )
                    
                    # Calculer les pourcentages
                    en_attente_percent = (jobs_en_attente / total_jobs * 100) if total_jobs > 0 else 0
                    en_cours_percent = (jobs_en_cours / total_jobs * 100) if total_jobs > 0 else 0
                    termines_percent = (jobs_termines / total_jobs * 100) if total_jobs > 0 else 0
                    
                    counting_stats.append({
                        'counting_id': counting.id,
                        'counting_reference': counting.reference,
                        'counting_order': counting.order,
                        'jobs_en_attente': {
                            'count': jobs_en_attente,
                            'percent': round(en_attente_percent, 2)
                        },
                        'jobs_en_cours': {
                            'count': jobs_en_cours,
                            'percent': round(en_cours_percent, 2)
                        },
                        'jobs_termines': {
                            'count': jobs_termines,
                            'percent': round(termines_percent, 2)
                        },
                        'total_jobs': total_jobs
                    })
                
                zone_stats.append({
                    'zone_id': zone.id,
                    'zone_reference': zone.reference,
                    'zone_name': zone.zone_name,
                    'status': zone_status,
                    'nombre_equipes': teams_count,
                    'nombre_jobs': jobs_count,
                    'countings': counting_stats
                })
            
            return zone_stats
            
        except JobCreationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors du calcul du monitoring par zone: {str(e)}")
            raise JobCreationError(f"Erreur lors du calcul du monitoring par zone: {str(e)}")
    
    def _calculate_zone_status(self, jobs: List[Job]) -> str:
        """
        Calcule le statut d'une zone basé sur les statuts des assignments des jobs.
        
        Règles :
        - Si tous les assignments ont le statut "TRANSFERT", alors le statut est "EN ATTENTE"
        - Si au moins un assignment a le statut "ENTAME", alors le statut est "EN COURS"
        - Si tous les assignments ont le statut "TERMINE", alors le statut est "TERMINE"
        - Sinon, le statut est "EN COURS" (par défaut)
        
        Args:
            jobs: Liste des jobs de la zone
            
        Returns:
            Statut de la zone : "EN ATTENTE", "EN COURS" ou "TERMINE"
        """
        if not jobs:
            return "EN ATTENTE"
        
        # Récupérer tous les assignments de tous les jobs de la zone
        all_assignments = []
        for job in jobs:
            all_assignments.extend(job.assigment_set.all())
        
        if not all_assignments:
            return "EN ATTENTE"
        
        # Vérifier si tous les assignments sont terminés
        all_termines = all(
            assignment.status == 'TERMINE' 
            for assignment in all_assignments
        )
        if all_termines:
            return "TERMINE"
        
        # Vérifier si au moins un assignment est entamé
        has_entame = any(
            assignment.status == 'ENTAME' 
            for assignment in all_assignments
        )
        if has_entame:
            return "EN COURS"
        
        # Vérifier si tous les assignments sont en transfert
        all_transfert = all(
            assignment.status == 'TRANSFERT' 
            for assignment in all_assignments
        )
        if all_transfert:
            return "EN ATTENTE"
        
        # Par défaut, si aucun des cas ci-dessus n'est vrai, on considère que c'est en cours
        return "EN COURS"

