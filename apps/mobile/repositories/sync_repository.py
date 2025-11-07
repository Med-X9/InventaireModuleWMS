from django.utils import timezone
from apps.inventory.models import Inventory, Job, Assigment, Counting, Setting, JobDetail
from apps.mobile.exceptions.inventory_exceptions import (
    InventoryNotFoundException,
    DatabaseConnectionException,
    DataValidationException
)


class SyncRepository:
    """Repository pour la synchronisation"""
    
    def get_inventories_in_realisation(self, inventory_id=None):
        """Récupère les inventaires en réalisation"""
        queryset = Inventory.objects.filter(status='EN REALISATION')
        if inventory_id:
            queryset = queryset.filter(id=inventory_id)
        return queryset
    
    def get_jobs_by_inventories(self, inventories):
        """Récupère les jobs pour les inventaires donnés avec leurs job_details préchargés"""
        return Job.objects.filter(
            inventory__in=inventories, 
            status__in=['TRANSFERT', 'ENTAME']
        ).prefetch_related(
            'jobdetail_set',
            'jobdetail_set__location',
            'jobdetail_set__location__sous_zone',
            'jobdetail_set__location__sous_zone__zone',
            'jobdetail_set__counting'
        )
    
    def get_jobs_by_inventories_and_user(self, inventories, user_id):
        """
        Récupère tous les jobs assignés à l'utilisateur, même s'ils sont dans d'autres inventaires

        Args:
            inventories: Queryset des inventaires (utilisé pour référence)

        Returns:
            Queryset des jobs assignés à l'utilisateur avec statut TRANSFERT uniquement
        """
        # Récupérer tous les assignments de l'utilisateur avec statut TRANSFERT uniquement
        job_ids = Assigment.objects.filter(
            session_id=user_id,
            job__status='TRANSFERT'
        ).values_list('job_id', flat=True).distinct()

        # Si aucun job trouvé, retourner un queryset vide
        if not job_ids:
            return Job.objects.none()

        # Récupérer les jobs avec leurs job_details préchargés
        return Job.objects.filter(
            id__in=job_ids
        ).prefetch_related(
            'jobdetail_set',
            'jobdetail_set__location',
            'jobdetail_set__location__sous_zone',
            'jobdetail_set__location__sous_zone__zone',
            'jobdetail_set__counting'
        )
    
    def get_inventories_by_user_assignments(self, user_id):
        """
        Récupère les inventaires liés aux jobs assignés à l'utilisateur avec statut EN REALISATION uniquement
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Queryset des inventaires EN REALISATION contenant des jobs TRANSFERT assignés à l'utilisateur
        """
        # Récupérer les IDs des inventaires des jobs assignés à l'utilisateur avec statut TRANSFERT uniquement
        inventory_ids = Assigment.objects.filter(
            session_id=user_id,
            job__status='TRANSFERT'
        ).values_list('job__inventory_id', flat=True).distinct()
        
        if not inventory_ids:
            return Inventory.objects.none()
        
        # Récupérer les inventaires avec statut EN REALISATION uniquement
        return Inventory.objects.filter(id__in=inventory_ids, status='EN REALISATION')
    
    def get_countings_by_user_assignments(self, user_id):
        """
        Récupère les comptages liés aux assignments de l'utilisateur pour les jobs TRANSFERT uniquement
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Queryset des countings des assignments de l'utilisateur pour les jobs TRANSFERT
        """
        # Récupérer les counting_id des assignments de l'utilisateur avec statut TRANSFERT uniquement
        counting_ids = Assigment.objects.filter(
            session_id=user_id,
            job__status='TRANSFERT'
        ).values_list('counting_id', flat=True).distinct()
        
        if not counting_ids:
            return Counting.objects.none()
        
        # Récupérer les countings
        return Counting.objects.filter(id__in=counting_ids)
    
    def get_assignments_by_jobs(self, jobs):
        """Récupère les assignations pour les jobs donnés"""
        return Assigment.objects.filter(job__in=jobs)
    
    def get_assignments_by_jobs_and_user(self, jobs, user_id):
        """
        Récupère les assignations pour les jobs donnés, filtrées par utilisateur
        
        Args:
            jobs: Queryset des jobs
            user_id: ID de l'utilisateur pour filtrer les assignments
            
        Returns:
            Queryset des assignments de l'utilisateur pour ces jobs
        """
        return Assigment.objects.filter(job__in=jobs, session_id=user_id)
    
    def get_countings_by_inventories(self, inventories):
        """Récupère les comptages pour les inventaires donnés"""
        return Counting.objects.filter(inventory__in=inventories)
    
    def get_warehouse_info_for_inventory(self, inventory):
        """Récupère les informations d'entrepôt pour un inventaire"""
        try:
            jobs = Job.objects.filter(inventory=inventory)
            if jobs.exists():
                first_job = jobs.first()
                return {
                    'warehouse_web_id': first_job.warehouse.id,
                    'warehouse_name': first_job.warehouse.warehouse_name
                }
            else:
                # Si pas de job, essayer via les settings
                settings = inventory.awi_links.all()
                if settings.exists():
                    first_setting = settings.first()
                    return {
                        'warehouse_web_id': first_setting.warehouse.id,
                        'warehouse_name': first_setting.warehouse.warehouse_name
                    }
                else:
                    print(f"Aucune information d'entrepôt trouvée pour l'inventaire {inventory.id}")
                    return {
                        'warehouse_web_id': None,
                        'warehouse_name': None
                    }
        except Exception as e:
            print(f"Erreur lors de la récupération des informations d'entrepôt pour l'inventaire {inventory.id}: {str(e)}")
            return {
                'warehouse_web_id': None,
                'warehouse_name': None
            }
    
    def get_inventories_by_user_account(self, user_id):
        """Récupère les inventaires du même compte qu'un utilisateur"""
        try:
            from apps.users.models import UserApp
            
            # Récupérer l'utilisateur
            user = UserApp.objects.get(id=user_id)
            
            # Récupérer le compte de l'utilisateur
            account = user.compte
            if not account:
                print(f"Aucun compte associé à l'utilisateur {user_id}")
                raise DataValidationException(f"Aucun compte associé à l'utilisateur {user_id}")
            
            # Récupérer tous les inventaires du même compte
            inventories = Inventory.objects.filter(
                awi_links__account=account,
                status='EN REALISATION'
            ).distinct().order_by('-created_at')
            
            return inventories
            
        except UserApp.DoesNotExist:
            print(f"Utilisateur avec l'ID {user_id} non trouvé")
            raise DataValidationException(f"Utilisateur avec l'ID {user_id} non trouvé")
        except Exception as e:
            print(f"Erreur lors de la récupération des inventaires du compte utilisateur: {str(e)}")
            raise DatabaseConnectionException(f"Erreur lors de la récupération des inventaires: {str(e)}")
    
    def format_inventory_data(self, inventory, warehouse_info):
        """Formate les données d'un inventaire"""
        return {
            'web_id': inventory.id,
            'reference': inventory.reference,
            'label': inventory.label,
            'date': inventory.date.isoformat(),
            'status': inventory.status,
            'inventory_type': inventory.inventory_type,
            'warehouse_web_id': warehouse_info['warehouse_web_id'],
            'warehouse_name': warehouse_info['warehouse_name'],
            'en_preparation_status_date': inventory.en_preparation_status_date.isoformat() if inventory.en_preparation_status_date else None,
            'en_realisation_status_date': inventory.en_realisation_status_date.isoformat() if inventory.en_realisation_status_date else None,
            'termine_status_date': inventory.termine_status_date.isoformat() if inventory.termine_status_date else None,
            'cloture_status_date': inventory.cloture_status_date.isoformat() if inventory.cloture_status_date else None,
            'created_at': inventory.created_at.isoformat(),
            'updated_at': inventory.updated_at.isoformat()
        }
    
    def format_job_detail_data(self, job_detail):
        """Formate les données essentielles d'un job_detail"""
        return {
            'web_id': job_detail.id,
            'reference': job_detail.reference,
            'status': job_detail.status,
            'location_web_id': job_detail.location.id if job_detail.location else None,
            'location_reference': job_detail.location.location_reference if job_detail.location else None,
            'counting_web_id': job_detail.counting.id if job_detail.counting else None
        }
    
    def format_job_data(self, job, user_id=None):
        """
        Formate les données d'un job avec ses job_details
        
        Args:
            job: Instance du Job
            user_id: ID de l'utilisateur pour filtrer les job_details par assignments (optionnel)
        """
        # Récupérer les job_details
        job_detail_queryset = job.jobdetail_set.all()
        
        # Filtrer les job_details par assignments de l'utilisateur si user_id est fourni
        if user_id:
            # Récupérer les counting_id des assignments de l'utilisateur pour ce job
            user_counting_ids = Assigment.objects.filter(
                job=job,
                session_id=user_id
            ).values_list('counting_id', flat=True).distinct()
            
            # Filtrer les job_details par counting
            if user_counting_ids:
                job_detail_queryset = job_detail_queryset.filter(
                    counting_id__in=user_counting_ids
                )
            else:
                # Si aucun assignment pour cet utilisateur, retourner une liste vide
                job_detail_queryset = job_detail_queryset.none()
        
        # Formater les job_details
        job_details = []
        for job_detail in job_detail_queryset:
            job_details.append(self.format_job_detail_data(job_detail))
        
        return {
            'web_id': job.id,
            'reference': job.reference,
            'status': job.status,
            'inventory_web_id': job.inventory.id,
            'warehouse_web_id': job.warehouse.id,
            'job_details': job_details,
            'en_attente_date': job.en_attente_date.isoformat() if job.en_attente_date else None,
            'affecte_date': job.affecte_date.isoformat() if job.affecte_date else None,
            'pret_date': job.pret_date.isoformat() if job.pret_date else None,
            'transfert_date': job.transfert_date.isoformat() if job.transfert_date else None,
            'entame_date': job.entame_date.isoformat() if job.entame_date else None,
            'valide_date': job.valide_date.isoformat() if job.valide_date else None,
            'termine_date': job.termine_date.isoformat() if job.termine_date else None,
            'created_at': job.created_at.isoformat(),
            'updated_at': job.updated_at.isoformat()
        }
    
    def format_assignment_data(self, assignment):
        """Formate les données d'une assignation"""
        return {
            'web_id': assignment.id,
            'reference': assignment.reference,
            'status': assignment.status,
            'job_web_id': assignment.job.id,
            'personne_web_id': assignment.personne.id if assignment.personne else None,
            'personne_two_web_id': assignment.personne_two.id if assignment.personne_two else None,
            'counting_web_id': assignment.counting.id,
            'session_web_id': assignment.session.id if assignment.session else None,
            'transfert_date': assignment.transfert_date.isoformat() if assignment.transfert_date else None,
            'entame_date': assignment.entame_date.isoformat() if assignment.entame_date else None,
            'affecte_date': assignment.affecte_date.isoformat() if assignment.affecte_date else None,
            'pret_date': assignment.pret_date.isoformat() if assignment.pret_date else None,
            'date_start': assignment.date_start.isoformat() if assignment.date_start else None,
            'created_at': assignment.created_at.isoformat(),
            'updated_at': assignment.updated_at.isoformat()
        }
    
    def format_counting_data(self, counting):
        """Formate les données d'un comptage"""
        return {
            'web_id': counting.id,
            'reference': counting.reference,
            'order': counting.order,
            'count_mode': counting.count_mode,
            'unit_scanned': counting.unit_scanned,
            'entry_quantity': counting.entry_quantity,
            'is_variant': counting.is_variant,
            'n_lot': counting.n_lot,
            'n_serie': counting.n_serie,
            'dlc': counting.dlc,
            'show_product': counting.show_product,
            'stock_situation': counting.stock_situation,
            'quantity_show': counting.quantity_show,
            'inventory_web_id': counting.inventory.id,
            'created_at': counting.created_at.isoformat(),
            'updated_at': counting.updated_at.isoformat()
        } 