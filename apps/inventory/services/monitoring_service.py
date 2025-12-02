"""
Service pour le monitoring par zone
"""
import logging
from typing import Dict, Any, List
from ..repositories.job_repository import JobRepository
from ..models import Job, Assigment, Counting, JobDetail
from ..exceptions.job_exceptions import JobCreationError

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Service pour calculer les statistiques de monitoring par zone
    et les statistiques globales par inventaire / entrepôt.
    
    Contient uniquement la logique métier (pas d'accès HTTP ou de sérialisation).
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
            from apps.masterdata.models import Zone
            
            # Vérifier que l'inventaire et l'entrepôt existent
            inventory = self.repository.get_inventory_by_id(inventory_id)
            warehouse = self.repository.get_warehouse_by_id(warehouse_id)
            if not inventory:
                raise JobCreationError(f"Inventaire avec l'ID {inventory_id} non trouvé")
            if not warehouse:
                raise JobCreationError(f"Entrepôt avec l'ID {warehouse_id} non trouvé")
            
            # Récupérer les zones de l'entrepôt (seulement les champs nécessaires)
            zones = Zone.objects.filter(
                warehouse_id=warehouse_id
            ).only('id', 'reference', 'zone_name').order_by('reference')
            
            # Récupérer les comptages de l'inventaire (seulement les champs nécessaires)
            countings = Counting.objects.filter(
                inventory_id=inventory_id
            ).only('id', 'reference', 'order').order_by('order')
            
            # Construire les statistiques par zone avec requêtes SQL optimisées
            zone_stats = []
            
            for zone in zones:
                # Compter les jobs distincts dans cette zone (via JobDetail)
                jobs_count = Job.objects.filter(
                    inventory_id=inventory_id,
                    warehouse_id=warehouse_id,
                    jobdetail__location__sous_zone__zone_id=zone.id
                ).distinct().count()
                
                # Compter les emplacements distincts dans cette zone
                emplacements_count = JobDetail.objects.filter(
                    job__inventory_id=inventory_id,
                    job__warehouse_id=warehouse_id,
                    location__sous_zone__zone_id=zone.id
                ).values('location_id').distinct().count()
                
                # Compter les équipes distinctes dans cette zone
                # Équipes par session
                teams_by_session = Assigment.objects.filter(
                    job__inventory_id=inventory_id,
                    job__warehouse_id=warehouse_id,
                    job__jobdetail__location__sous_zone__zone_id=zone.id,
                    session__isnull=False
                ).values('session_id').distinct().count()
                
                # Équipes par personnes (sans session)
                teams_by_persons = Assigment.objects.filter(
                    job__inventory_id=inventory_id,
                    job__warehouse_id=warehouse_id,
                    job__jobdetail__location__sous_zone__zone_id=zone.id,
                    session__isnull=True
                ).values('personne_id', 'personne_two_id').distinct().count()
                
                teams_count = teams_by_session + teams_by_persons
                
                # Calculer le statut de la zone avec une requête optimisée
                zone_status = self._calculate_zone_status_optimized(
                    inventory_id, warehouse_id, zone.id
                )
                
                # Calculer les statistiques par comptage avec requêtes SQL optimisées
                counting_stats = []
                for counting in countings:
                    # Compter les jobs de cette zone qui ont un assignment pour ce comptage
                    nombre_jobs = Job.objects.filter(
                        inventory_id=inventory_id,
                        warehouse_id=warehouse_id,
                        jobdetail__location__sous_zone__zone_id=zone.id,
                        assigment__counting_id=counting.id
                    ).distinct().count()
                    
                    # Compter les emplacements distincts pour ce comptage dans cette zone
                    emplacements_counting_count = JobDetail.objects.filter(
                        job__inventory_id=inventory_id,
                        job__warehouse_id=warehouse_id,
                        location__sous_zone__zone_id=zone.id,
                        counting_id=counting.id
                    ).values('location_id').distinct().count()
                    
                    counting_stats.append({
                        'counting_id': counting.id,
                        'counting_reference': counting.reference,
                        'counting_order': counting.order,
                        'nombre_jobs': nombre_jobs,
                        'nombre_emplacements': emplacements_counting_count
                    })
                
                zone_stats.append({
                    'zone_id': zone.id,
                    'zone_reference': zone.reference,
                    'zone_name': zone.zone_name,
                    'status': zone_status,
                    'nombre_equipes': teams_count,
                    'nombre_jobs': jobs_count,
                    'nombre_emplacements': emplacements_count,
                    'countings': counting_stats
                })
            
            return zone_stats
            
        except JobCreationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors du calcul du monitoring par zone: {str(e)}")
            raise JobCreationError(f"Erreur lors du calcul du monitoring par zone: {str(e)}")

    def get_global_monitoring_by_inventory_and_warehouse(
        self,
        inventory_id: int,
        warehouse_id: int
    ) -> Dict[str, Any]:
        """
        Récupère les statistiques globales (toutes zones confondues) pour un
        inventaire et un entrepôt.

        Retourne :
        - total_equipes : nombre d'équipes distinctes affectées
        - total_jobs : nombre de jobs affectés
        - countings : pour les comptages d'ordre 1, 2 et 3 :
            - counting_id
            - counting_reference
            - counting_order
            - jobs_termines : nombre de jobs terminés pour ce comptage
            - jobs_termines_percent : pourcentage de jobs terminés par rapport au total_jobs
        """
        try:
            # Vérifier que l'inventaire et l'entrepôt existent
            inventory = self.repository.get_inventory_by_id(inventory_id)
            warehouse = self.repository.get_warehouse_by_id(warehouse_id)
            if not inventory:
                raise JobCreationError(
                    f"Inventaire avec l'ID {inventory_id} non trouvé"
                )
            if not warehouse:
                raise JobCreationError(
                    f"Entrepôt avec l'ID {warehouse_id} non trouvé"
                )

            # Récupérer les comptages de l'inventaire (ordre 1, 2, 3)
            countings = Counting.objects.filter(
                inventory_id=inventory_id,
                order__in=[1, 2, 3]
            ).order_by('order').only('id', 'order', 'reference')

            # Compter les jobs qui ont au moins un assignment (jobs affectés)
            # Utilisation d'une sous-requête optimisée
            total_jobs = Job.objects.filter(
                inventory_id=inventory_id,
                warehouse_id=warehouse_id
            ).filter(
                assigment__isnull=False
            ).distinct().count()

            # Calcul du nombre d'équipes distinctes avec une requête optimisée
            # Une équipe est identifiée par :
            # - la session si elle existe
            # - sinon la combinaison (personne, personne_two)
            
            # Compter les équipes distinctes via session
            teams_by_session = Assigment.objects.filter(
                job__inventory_id=inventory_id,
                job__warehouse_id=warehouse_id,
                session__isnull=False
            ).values('session_id').distinct().count()
            
            # Compter les équipes distinctes via personnes (sans session)
            teams_by_persons = Assigment.objects.filter(
                job__inventory_id=inventory_id,
                job__warehouse_id=warehouse_id,
                session__isnull=True
            ).values('personne_id', 'personne_two_id').distinct().count()
            
            total_equipes = teams_by_session + teams_by_persons

            # Statistiques par comptage avec requêtes optimisées
            counting_stats: List[Dict[str, Any]] = []

            for counting in countings:
                # Compter les jobs qui ont un assignment pour ce comptage
                jobs_with_counting = Job.objects.filter(
                    inventory_id=inventory_id,
                    warehouse_id=warehouse_id,
                    assigment__counting_id=counting.id
                ).distinct().count()

                # Compter les jobs terminés pour ce comptage
                # LOGIQUE : Un job est terminé pour un comptage si l'ASSIGNMENT de ce comptage a le statut 'TERMINE'
                # (pas le statut du job lui-même, car un job peut avoir plusieurs assignments pour différents comptages)
                # IMPORTANT : On filtre strictement sur TERMINE uniquement (pas PRET, pas ENTAME, etc.)
                jobs_termines = Job.objects.filter(
                    inventory_id=inventory_id,
                    warehouse_id=warehouse_id
                ).filter(
                    id__in=Assigment.objects.filter(
                        counting_id=counting.id,
                        status='TERMINE'
                    ).values_list('job_id', flat=True)
                ).distinct().count()

                jobs_termines_percent = (
                    (jobs_termines / total_jobs * 100) if total_jobs > 0 else 0
                )

                counting_stats.append(
                    {
                        "counting_id": counting.id,
                        "counting_order": counting.order,
                        "jobs_termines": jobs_termines,
                        "jobs_termines_percent": round(
                            jobs_termines_percent, 2
                        ),
                    }
                )

            return {
                "total_equipes": total_equipes,
                "total_jobs": total_jobs,
                "countings": counting_stats,
            }
            
        except JobCreationError:
            raise
        except Exception as e:
            logger.error(
                f"Erreur lors du calcul du monitoring global: {str(e)}"
            )
            raise JobCreationError(
                f"Erreur lors du calcul du monitoring global: {str(e)}"
            )
    
    def _calculate_zone_status_optimized(
        self,
        inventory_id: int,
        warehouse_id: int,
        zone_id: int
    ) -> str:
        """
        Calcule le statut d'une zone basé sur les statuts des assignments des jobs (version optimisée).
        
        Règles :
        - Si tous les assignments ont le statut "TRANSFERT", alors le statut est "EN ATTENTE"
        - Si au moins un assignment a le statut "ENTAME", alors le statut est "EN COURS"
        - Si tous les assignments ont le statut "TERMINE", alors le statut est "TERMINE"
        - Sinon, le statut est "EN COURS" (par défaut)
        
        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt
            zone_id: ID de la zone
            
        Returns:
            Statut de la zone : "EN ATTENTE", "EN COURS" ou "TERMINE"
        """
        from django.db.models import Count, Q
        
        # Compter les assignments par statut dans cette zone
        assignments_stats = Assigment.objects.filter(
            job__inventory_id=inventory_id,
            job__warehouse_id=warehouse_id,
            job__jobdetail__location__sous_zone__zone_id=zone_id
        ).values('status').annotate(count=Count('id'))
        
        if not assignments_stats.exists():
            return "EN ATTENTE"
        
        # Créer un dictionnaire des comptages par statut
        status_counts = {stat['status']: stat['count'] for stat in assignments_stats}
        total_assignments = sum(status_counts.values())
        
        # Vérifier si tous les assignments sont terminés
        if status_counts.get('TERMINE', 0) == total_assignments:
            return "TERMINE"
        
        # Vérifier si au moins un assignment est entamé
        if status_counts.get('ENTAME', 0) > 0:
            return "EN COURS"
        
        # Vérifier si tous les assignments sont en transfert
        if status_counts.get('TRANSFERT', 0) == total_assignments:
            return "EN ATTENTE"
        
        # Par défaut, si aucun des cas ci-dessus n'est vrai, on considère que c'est en cours
        return "EN COURS"
    
    def _calculate_zone_status(self, jobs: List[Job]) -> str:
        """
        Calcule le statut d'une zone basé sur les statuts des assignments des jobs.
        (Méthode legacy conservée pour compatibilité)
        
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

