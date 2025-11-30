from typing import List, Dict, Any, Optional
from django.db.models import Prefetch
from ..models import Job, JobDetail, Assigment, Counting, CountingDetail


class JobExportRepository:
    """
    Repository pour l'export des jobs prêts
    Contient uniquement les opérations d'accès aux données
    """
    
    def get_ready_jobs_by_inventory_and_warehouse(
        self,
        inventory_id: int,
        warehouse_id: int
    ) -> List[Job]:
        """
        Récupère les jobs avec assignments PRET ou TRANSFERT pour un inventaire et un warehouse
        Utilise la même logique que l'API PDF : récupère les jobs via les assignments
        
        Filtre par statut des assignments: TRANSFERT, PRET uniquement
        Filtre par statut des jobs: TRANSFERT, PRET uniquement
        
        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt
            
        Returns:
            Liste des jobs avec leurs relations préchargées
        """
        # Récupérer les job IDs via Assigment qui ont des assignments PRET ou TRANSFERT
        # C'est la même logique que l'API PDF
        job_ids = Assigment.objects.filter(
            job__inventory_id=inventory_id,
            job__warehouse_id=warehouse_id,
            job__status__in=['TRANSFERT', 'PRET'],
            status__in=['TRANSFERT', 'PRET']  # Filtrer uniquement les assignments PRET ou TRANSFERT (exclure ENTAME)
        ).values_list('job_id', flat=True).distinct()
        
        if not job_ids:
            return []
        
        return list(
            Job.objects.filter(
                id__in=job_ids,
                inventory_id=inventory_id,
                warehouse_id=warehouse_id,
                status__in=['TRANSFERT', 'PRET']
            ).select_related(
                'warehouse',
                'inventory'
            ).prefetch_related(
                Prefetch(
                    'jobdetail_set',
                    queryset=JobDetail.objects.select_related('location').order_by('location_id', '-id')
                ),
                Prefetch(
                    'assigment_set',
                    queryset=Assigment.objects.filter(
                        status__in=['TRANSFERT', 'PRET']
                    ).select_related(
                        'counting',
                        'session'
                    ).order_by('counting__order')
                )
            ).order_by('reference')
        )
    
    def get_counting_details_by_job_and_counting(
        self,
        job_id: int,
        counting_id: int,
        location_id: int
    ) -> Optional[CountingDetail]:
        """
        Récupère un CountingDetail pour un job, counting et location
        
        Args:
            job_id: ID du job
            counting_id: ID du comptage
            location_id: ID de l'emplacement
            
        Returns:
            CountingDetail ou None
        """
        try:
            return CountingDetail.objects.get(
                job_id=job_id,
                counting_id=counting_id,
                location_id=location_id
            )
        except CountingDetail.DoesNotExist:
            return None
    
    def get_counting_details_by_jobs_and_countings(
        self,
        job_ids: List[int],
        counting_ids: List[int]
    ) -> Dict[tuple, List[CountingDetail]]:
        """
        Récupère tous les CountingDetail pour des jobs et countings donnés
        
        Args:
            job_ids: Liste des IDs de jobs
            counting_ids: Liste des IDs de countings
            
        Returns:
            Dictionnaire avec clé (job_id, counting_id, location_id) et valeur liste de CountingDetail
        """
        counting_details = CountingDetail.objects.filter(
            job_id__in=job_ids,
            counting_id__in=counting_ids
        ).select_related('location', 'product', 'counting', 'job')
        
        # Créer un dictionnaire pour accès rapide
        # Peut y avoir plusieurs CountingDetail pour la même location (différents produits)
        result = {}
        for cd in counting_details:
            key = (cd.job_id, cd.counting_id, cd.location_id)
            if key not in result:
                result[key] = []
            result[key].append(cd)
        
        return result
    
    def get_countings_by_inventory_ordered(
        self,
        inventory_id: int
    ) -> List[Counting]:
        """
        Récupère les comptages d'un inventaire triés par ordre
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            Liste des comptages triés par ordre
        """
        return list(
            Counting.objects.filter(
                inventory_id=inventory_id
            ).order_by('order')
        )

