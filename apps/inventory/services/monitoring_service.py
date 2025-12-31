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

        Regroupe par zone :
        - nombre_jobs : nombre de jobs dans la zone
        - nombre_emplacements : nombre d'emplacements (jobdetail) dans la zone

        Pour chaque comptage d'ordre (1, 2, 3), retourne :
        - nombre et pourcentage de jobs avec statut assignment (TERMINE/ENTAME/TERMINE)

        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt

        Returns:
            Liste des statistiques par zone avec les comptages détaillés

        Raises:
            JobCreationError: Si une erreur survient
        """
        try:
            from apps.masterdata.models import Zone
            from django.db.models import Count

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

            # Récupérer les comptages de l'inventaire (ordres 1, 2, 3)
            countings = Counting.objects.filter(
                inventory_id=inventory_id,
                order__in=[1, 2, 3]
            ).only('id', 'reference', 'order').order_by('order')

            # Construire les statistiques par zone
            zone_stats = []

            for zone in zones:
                # Compter le nombre de jobs distincts qui ont des jobdetails dans cette zone
                nombre_jobs = Job.objects.filter(
                    inventory_id=inventory_id,
                    warehouse_id=warehouse_id,
                    jobdetail__location__sous_zone__zone_id=zone.id
                ).distinct().count()

                # Compter le nombre d'emplacements (jobdetails) dans cette zone
                nombre_emplacements = JobDetail.objects.filter(
                    job__inventory_id=inventory_id,
                    job__warehouse_id=warehouse_id,
                    location__sous_zone__zone_id=zone.id
                ).distinct().count()

                # Calculer les statistiques détaillées par comptage
                counting_stats = []
                for counting in countings:
                    counting_detail = self._get_counting_assignment_stats_by_zone(
                        inventory_id, warehouse_id, zone.id, counting
                    )
                    counting_stats.append(counting_detail)

                zone_stats.append({
                    'zone_id': zone.id,
                    'zone_reference': zone.reference,
                    'zone_name': zone.zone_name,
                    'nombre_jobs': nombre_jobs,
                    'nombre_emplacements': nombre_emplacements,
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
    
    def _get_counting_assignment_stats_by_zone(
        self,
        inventory_id: int,
        warehouse_id: int,
        zone_id: int,
        counting: Counting
    ) -> Dict[str, Any]:
        """
        Récupère les statistiques des assignments pour un comptage spécifique dans une zone.

        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt
            zone_id: ID de la zone
            counting: Instance du comptage

        Returns:
            Dictionnaire avec les statistiques d'assignments pour ce comptage
        """
        from django.db.models import Count

        # Compter les assignments par statut pour ce comptage dans cette zone
        job_stats = Assigment.objects.filter(
            job__inventory_id=inventory_id,
            job__warehouse_id=warehouse_id,
            job__jobdetail__location__sous_zone__zone_id=zone_id,
            counting_id=counting.id
        ).values('status').annotate(count=Count('id')).order_by('status')

        # Créer un dictionnaire des comptages par statut
        status_counts = {stat['status']: stat['count'] for stat in job_stats}

        # Calculer le total des assignments pour ce comptage dans cette zone
        total_assignments = sum(status_counts.values())

        # Calculer les statistiques pour les statuts demandés (TERMINE, ENTAME, TERMINE)
        # Note: L'utilisateur a demandé "termine / entame / termine" - je pense qu'il veut TERMINE, ENTAME, TERMINE
        # Mais cela semble être une répétition, je vais assumer qu'il veut les 3 statuts principaux
        assignments_stats = []
        relevant_statuses = ['TERMINE', 'ENTAME', 'TRANSFERT']

        for status in relevant_statuses:
            count = status_counts.get(status, 0)
            percentage = (count / total_assignments * 100) if total_assignments > 0 else 0

            assignments_stats.append({
                'status': status,
                'count': count,
                'percentage': round(percentage, 2)
            })

        return {
            'counting_id': counting.id,
            'counting_reference': counting.reference,
            'counting_order': counting.order,
            'assignments': assignments_stats
        }

    def _calculate_zone_status_optimized(
        self,
        inventory_id: int,
        warehouse_id: int,
        zone_id: int
    ) -> str:
        """
        Calcule le statut d'une zone basé sur les statuts des assignments (version optimisée).

        Règles basées sur les assignments :
        - "EN ATTENTE" : tous les assignments sont en status "TRANSFERT"
        - "EN COURS" : au moins un assignment est en status "ENTAME"
        - "TERMINE" : tous les assignments sont en status "TERMINE"
        - Sinon, le statut est "EN COURS" (par défaut)

        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt
            zone_id: ID de la zone

        Returns:
            Statut de la zone : "EN ATTENTE", "EN COURS" ou "TERMINE"
        """
        from django.db.models import Count

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

        Règles basées sur les assignments :
        - "EN ATTENTE" : tous les assignments sont en status "TRANSFERT"
        - "EN COURS" : au moins un assignment est en status "ENTAME"
        - "TERMINE" : tous les assignments sont en status "TERMINE"
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

        # Compter les assignments par statut
        status_counts = {}
        for assignment in all_assignments:
            status_counts[assignment.status] = status_counts.get(assignment.status, 0) + 1

        total_assignments = len(all_assignments)

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

