"""
Repository pour les opérations de données pour la génération PDF
"""
from typing import List, Optional
from django.db import DatabaseError
from ..interfaces.pdf_interface import PDFRepositoryInterface
from ..models import Inventory, Counting, Job, JobDetail, Assigment, CountingDetail
from ..exceptions.pdf_exceptions import PDFRepositoryError
from apps.masterdata.models import Stock
import logging

logger = logging.getLogger(__name__)


class PDFRepository(PDFRepositoryInterface):
    """Repository pour la génération PDF"""
    
    def get_inventory_by_id(self, inventory_id: int) -> Optional[Inventory]:
        """Récupère un inventaire par ID"""
        try:
            return Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            logger.warning(f"Inventaire avec l'ID {inventory_id} non trouvé")
            return None
        except DatabaseError as e:
            logger.error(f"Erreur de base de données lors de la récupération de l'inventaire {inventory_id}: {str(e)}")
            raise PDFRepositoryError(f"Erreur de base de données lors de la récupération de l'inventaire: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération de l'inventaire {inventory_id}: {str(e)}", exc_info=True)
            raise PDFRepositoryError(f"Erreur lors de la récupération de l'inventaire: {str(e)}")
    
    def get_counting_by_id(self, counting_id: int) -> Optional[Counting]:
        """Récupère un comptage par ID"""
        try:
            return Counting.objects.get(id=counting_id)
        except Counting.DoesNotExist:
            return None
    
    def get_countings_by_inventory(self, inventory: Inventory) -> List[Counting]:
        """Récupère tous les comptages d'un inventaire"""
        return list(Counting.objects.filter(inventory=inventory).order_by('order'))
    
    def get_countings_by_inventory_and_orders(self, inventory: Inventory, orders: List[int]) -> List[Counting]:
        """Récupère les comptages d'un inventaire avec les ordres spécifiés (requête optimisée)"""
        return list(
            Counting.objects.filter(
                inventory=inventory,
                order__in=orders
            ).order_by('order')
        )
    
    def get_all_jobs_by_inventory(self, inventory: Inventory) -> List[Job]:
        """Récupère tous les jobs d'un inventaire avec leurs détails"""
        return list(
            Job.objects.filter(
                inventory=inventory
            ).prefetch_related(
                'jobdetail_set__location',
                'assigment_set__counting',
                'assigment_set__session',
                'assigment_set__personne',
                'assigment_set__personne_two'
            )
        )
    
    def get_job_details_by_job(self, job: Job) -> List[JobDetail]:
        """Récupère les job details d'un job"""
        return list(
            job.jobdetail_set.select_related('location', 'counting').all()
        )
    
    def get_stocks_by_location_and_inventory(
        self, 
        location: 'Location', 
        inventory: Inventory
    ) -> List[Stock]:
        """Récupère les stocks d'un emplacement pour un inventaire"""
        return list(
            Stock.objects.filter(
                location=location,
                inventory=inventory
            ).select_related('product', 'unit_of_measure')
        )
    
    def get_jobs_by_counting(self, inventory: Inventory, counting: Counting) -> List[Job]:
        """
        Récupère les jobs d'un inventaire pour un comptage spécifique
        Filtre par statut des assignments: TRANSFERT, PRET uniquement
        Filtre par statut des jobs: TRANSFERT, PRET uniquement
        Recherche via Assigment.counting (relation principale)
        """
        # Récupérer les job IDs via Assigment qui ont ce comptage
        # C'est la relation principale : un job est lié à un counting via ses assignments
        job_ids = Assigment.objects.filter(
            job__inventory=inventory,
            counting=counting,
            job__status__in=['TRANSFERT', 'PRET'],
            status__in=['TRANSFERT', 'PRET']  # Filtrer uniquement les assignments PRET ou TRANSFERT (exclure ENTAME)
        ).values_list('job_id', flat=True).distinct()
        
        if not job_ids:
            return []
        
        return list(
            Job.objects.filter(
                id__in=job_ids,
                status__in=['TRANSFERT', 'PRET']
            ).prefetch_related(
                'jobdetail_set__location',
                'assigment_set__counting',
                'assigment_set__session',
                'assigment_set__personne',
                'assigment_set__personne_two'
            ).order_by('reference')
        )
    
    def get_assignments_by_job(self, job: Job) -> List[Assigment]:
        """Récupère les assignments d'un job"""
        return list(
            job.assigment_set.select_related(
                'counting',
                'session',
                'personne',
                'personne_two'
            ).all()
        )
    
    def get_assignments_by_inventory(
        self, 
        inventory: Inventory, 
        job_ids: Optional[List[int]] = None
    ) -> List[Assigment]:
        """
        Récupère tous les assignments d'un inventaire avec counting.order et session
        Filtre par statut des assignments: TRANSFERT, PRET uniquement
        Filtre par statut des jobs: TRANSFERT, PRET uniquement
        Récupère tous les ordres de comptage (pas de restriction d'ordre)
        Si job_ids est fourni, filtre uniquement les assignments de ces jobs
        
        Args:
            inventory: L'inventaire
            job_ids: Liste optionnelle des IDs de jobs à filtrer (si None, récupère tous les jobs)
            
        Returns:
            Liste des assignments correspondants
            
        Raises:
            PDFRepositoryError: Si une erreur survient lors de la récupération
        """
        try:
            queryset = Assigment.objects.filter(
                job__inventory=inventory,
                job__status__in=['TRANSFERT', 'PRET'],
                status__in=['TRANSFERT', 'PRET']  # Filtrer uniquement les assignments PRET ou TRANSFERT (exclure ENTAME)
                # Pas de filtre sur counting__order : récupère tous les ordres de comptage
            )
            
            # Si job_ids est fourni, filtrer uniquement ces jobs
            if job_ids:
                queryset = queryset.filter(job_id__in=job_ids)
            
            assignments = list(
                queryset.select_related(
                    'job',
                    'counting',
                    'session',
                    'personne',
                    'personne_two'
                ).prefetch_related(
                    'job__jobdetail_set__location'
                ).order_by('counting__order', 'job__reference')
            )
            
            logger.info(f"Récupération de {len(assignments)} assignments pour l'inventaire {inventory.id}")
            return assignments
            
        except DatabaseError as e:
            logger.error(f"Erreur de base de données lors de la récupération des assignments: {str(e)}")
            raise PDFRepositoryError(f"Erreur de base de données lors de la récupération des assignments: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des assignments: {str(e)}", exc_info=True)
            raise PDFRepositoryError(f"Erreur lors de la récupération des assignments: {str(e)}")
    
    def get_assignment_by_id(self, assignment_id: int) -> Optional[Assigment]:
        """Récupère un assignment par ID"""
        try:
            return Assigment.objects.select_related(
                'counting',
                'session',
                'personne',
                'personne_two',
                'job',
                'job__inventory'
            ).get(id=assignment_id)
        except Assigment.DoesNotExist:
            return None
    
    def get_job_by_id(self, job_id: int) -> Optional[Job]:
        """Récupère un job par ID"""
        try:
            return Job.objects.select_related(
                'inventory',
                'warehouse'
            ).prefetch_related(
                'assigment_set__counting',
                'assigment_set__session',
                'assigment_set__personne',
                'assigment_set__personne_two'
            ).get(id=job_id)
        except Job.DoesNotExist:
            return None
    
    def get_counting_details_by_job_and_counting(
        self, 
        job: Job, 
        counting: Counting
    ) -> List[CountingDetail]:
        """Récupère les counting details d'un job pour un comptage spécifique"""
        return list(
            CountingDetail.objects.filter(
                job=job,
                counting=counting
            ).select_related(
                'location',
                'product',
                'counting',
                'job'
            ).order_by('location__location_reference', 'product__Barcode')
        )
