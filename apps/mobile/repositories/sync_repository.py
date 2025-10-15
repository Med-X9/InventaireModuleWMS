from django.utils import timezone
from apps.inventory.models import Inventory, Job, Assigment, Counting, Setting
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
        """Récupère les jobs pour les inventaires donnés avec statut TRANSFERT ou ENTAME"""
        return Job.objects.filter(
            inventory__in=inventories,
            status__in=['TRANSFERT', 'ENTAME']
        )
    
    def get_assignments_by_jobs(self, jobs):
        """Récupère les assignations pour les jobs donnés"""
        return Assigment.objects.filter(job__in=jobs)
    
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
    
    def format_job_data(self, job):
        """Formate les données d'un job"""
        return {
            'web_id': job.id,
            'reference': job.reference,
            'status': job.status,
            'inventory_web_id': job.inventory.id,
            'warehouse_web_id': job.warehouse.id,
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