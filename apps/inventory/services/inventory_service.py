"""
Service pour la gestion des inventaires.
"""
from typing import Dict, Any, List
from django.utils import timezone
from ..repositories import InventoryRepository
from ..exceptions import InventoryValidationError, InventoryNotFoundError
from ..models import Inventory, Setting, Counting, CountingDetail
from django.db import IntegrityError
import logging
from .counting_service import CountingService
from apps.masterdata.models import Warehouse
from apps.inventory.usecases.inventory_launch_validation import InventoryLaunchValidationUseCase

# Configuration du logger
logger = logging.getLogger(__name__)

class InventoryService:
    """Service pour la gestion des inventaires."""
    
    def __init__(self, repository: InventoryRepository = None):
        self.repository = repository or InventoryRepository()
        self.counting_service = CountingService()
    
    def validate_inventory_data(self, data: Dict[str, Any]) -> None:
        """
        Valide les données d'un inventaire.
        
        Args:
            data: Les données à valider
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        errors = []
        
        if not data.get('label'):
            errors.append("Le label est obligatoire")
        
        if not data.get('date'):
            errors.append("La date est obligatoire")
        
        if not data.get('account'):
            errors.append("Le compte est obligatoire")
        
        if not data.get('warehouse'):
            errors.append("Au moins un entrepôt est obligatoire")
        
        # Validation du type d'inventaire
        inventory_type = data.get('inventory_type', 'GENERAL')
        if inventory_type not in ['TOURNANT', 'GENERAL']:
            errors.append("Le type d'inventaire doit être 'TOURNANT' ou 'GENERAL'")
        
        comptages = data.get('comptages', [])
        if not comptages:
            errors.append("Les comptages sont obligatoires")
        else:
            # Validation des comptages avec le service de comptage
            try:
                # Validation de la cohérence des modes de comptage
                self.counting_service.validate_countings_consistency(comptages)
                
                # Validation de chaque comptage individuellement
                for comptage in comptages:
                    self.counting_service.validate_counting_data(comptage)
            except Exception as e:
                errors.append(str(e))
        
        if errors:
            raise InventoryValidationError(" | ".join(errors))

    def _validate_countings(self, comptages: List[Dict[str, Any]]) -> List[str]:
        """Valide les comptages."""
        errors = []
        for i, comptage in enumerate(comptages, 1):
            if not comptage.get('order'):
                errors.append(f"L'ordre est obligatoire pour le comptage {i}")
            if not comptage.get('count_mode'):
                errors.append(f"Le mode de comptage est obligatoire pour le comptage {i}")
        return errors

    def validate_counting_modes(self, comptages: List[Dict[str, Any]]) -> List[str]:
        """Valide les modes de comptage."""
        errors = []
        valid_modes = ['en vrac', 'par article']
        for i, comptage in enumerate(comptages, 1):
            if comptage.get('count_mode') not in valid_modes:
                errors.append(f"Mode de comptage invalide pour le comptage {i}")
        return errors
    
    def create_inventory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouvel inventaire en utilisant le use case de gestion.
        
        Args:
            data: Les données de l'inventaire
            
        Returns:
            Dict[str, Any]: Résultat de la création
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        try:
            # Utilisation du use case de gestion pour la création
            from ..usecases.inventory_management import InventoryManagementUseCase
            use_case = InventoryManagementUseCase()
            result = use_case.create(data)
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'inventaire: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors de la création de l'inventaire: {str(e)}")

    def delete_inventory(self, inventory_id: int) -> None:
        """
        Effectue un soft delete d'un inventaire si son statut est en attente.
        
        Args:
            inventory_id: L'ID de l'inventaire à supprimer
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            InventoryValidationError: Si l'inventaire ne peut pas être supprimé
        """
        try:
            inventory = self.repository.get_by_id(inventory_id)
            
            if inventory.status != 'EN ATTENTE':
                raise InventoryValidationError(
                    "Seuls les inventaires en attente peuvent être supprimés"
                )
            
            # Soft delete de l'inventaire
            inventory.hard_delete()
            
            
        except InventoryNotFoundError:
            raise
        except InventoryValidationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'inventaire: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors de la suppression de l'inventaire: {str(e)}")

    def get_inventory_by_id(self, inventory_id: int) -> Inventory:
        """
        Récupère un inventaire par son ID.
        
        Args:
            inventory_id: L'ID de l'inventaire à récupérer
            
        Returns:
            Inventory: L'inventaire trouvé
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
        """
        try:
            return self.repository.get_by_id(inventory_id)
        except Inventory.DoesNotExist:
            logger.error(f"Inventaire non trouvé avec l'ID: {inventory_id}")
            raise InventoryNotFoundError("L'inventaire demandé n'existe pas")

    def get_inventory_by_reference(self, reference: str) -> Inventory:
        """
        Récupère un inventaire par sa référence.
        
        Args:
            reference: La référence de l'inventaire
            
        Returns:
            Inventory: L'inventaire trouvé
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
        """
        try:
            return self.repository.get_by_reference(reference)
        except Inventory.DoesNotExist:
            logger.error(f"Inventaire non trouvé avec la référence: {reference}")
            raise InventoryNotFoundError("L'inventaire demandé n'existe pas")

    def get_inventory_with_related_data_by_reference(self, reference: str) -> Inventory:
        """
        Récupère un inventaire avec ses données liées par sa référence.
        
        Args:
            reference: La référence de l'inventaire
            
        Returns:
            Inventory: L'inventaire trouvé avec ses données liées
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
        """
        try:
            return self.repository.get_with_related_data_by_reference(reference)
        except Inventory.DoesNotExist:
            logger.error(f"Inventaire non trouvé avec la référence: {reference}")
            raise InventoryNotFoundError("L'inventaire demandé n'existe pas")

    def update_inventory(self, inventory_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un inventaire en utilisant le use case de gestion.
        
        Args:
            inventory_id: L'ID de l'inventaire à mettre à jour
            data: Les nouvelles données de l'inventaire
            
        Returns:
            Dict[str, Any]: Résultat de la mise à jour
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            InventoryValidationError: Si les données sont invalides
        """
        try:
            # Utilisation du use case de gestion pour la mise à jour
            from ..usecases.inventory_management import InventoryManagementUseCase
            use_case = InventoryManagementUseCase()
            result = use_case.update(inventory_id, data)
            return result
            
        except InventoryNotFoundError:
            raise
        except InventoryValidationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'inventaire: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors de la mise à jour de l'inventaire: {str(e)}")

    def _check_stocks_exist(self, warehouses: List[Warehouse], inventory_id: int) -> bool:
        """
        Vérifie si des stocks existent pour les entrepôts donnés.
        
        Args:
            warehouses: Liste des entrepôts à vérifier
            inventory_id: L'ID de l'inventaire
            
        Returns:
            bool: True si des stocks existent, False sinon
        """
        from apps.masterdata.models import Stock
        
        for warehouse in warehouses:
            stocks_count = Stock.objects.filter(
                location__sous_zone__zone__warehouse=warehouse,
                location__is_active=True,
                location__sous_zone__zone__zone_status='ACTIVE',
                is_deleted=False,
                inventory_id=inventory_id
            ).count()
            
            logger.info(f"Nombre de stocks trouvés pour l'entrepôt {warehouse.warehouse_name}: {stocks_count}")
            
            if stocks_count > 0:
                return True
        return False

    def _create_inventory_details_from_stocks(self, counting: Counting, warehouses: List[Warehouse], inventory_id: int) -> None:
        """
        Crée les détails d'inventaire à partir des stocks existants.
        
        Args:
            counting: Le comptage pour lequel créer les détails
            warehouses: Liste des entrepôts à traiter
            inventory_id: L'ID de l'inventaire
        """
        from apps.masterdata.models import Stock
        
        for warehouse in warehouses:
            stocks = Stock.objects.filter(
                location__sous_zone__zone__warehouse=warehouse,
                location__is_active=True,
                location__sous_zone__zone__zone_status='ACTIVE',
                is_deleted=False,
                inventory_id=inventory_id
            ).select_related('product', 'location', 'location__sous_zone', 'location__sous_zone__zone')
            
            stocks_count = stocks.count()
            logger.info(f"Création de {stocks_count} détails d'inventaire pour l'entrepôt {warehouse.warehouse_name}")
            
            for stock in stocks:
                quantity = int(stock.quantity_available)
                CountingDetail.objects.create(
                    counting=counting,
                    product=stock.product,
                    location=stock.location,
                    quantity_inventoried=quantity
                )

    def _handle_etat_stock_mode(self, first_counting: Counting, warehouses: List[Warehouse], inventory_id: int) -> None:
        """
        Gère le mode "Etat de stock" pour le premier comptage.
        
        Args:
            first_counting: Le premier comptage
            warehouses: Liste des entrepôts à traiter
            inventory_id: L'ID de l'inventaire
            
        Raises:
            InventoryValidationError: Si aucun stock n'est trouvé
        """
        if not self._check_stocks_exist(warehouses, inventory_id):
            warehouse_names = [w.warehouse_name for w in warehouses]
            logger.warning(f"Aucun stock trouvé pour les entrepôts: {', '.join(warehouse_names)}")
            raise InventoryValidationError(
                "Aucun stock trouvé pour les entrepôts de cet inventaire"
            )
        
        self._create_inventory_details_from_stocks(first_counting, warehouses, inventory_id)
        
        # Note: Le comptage n'a plus de champ status, donc on ne met plus à jour le statut

    # def _handle_liste_emplacement_article_mode(self, warehouses: List[Warehouse]) -> None:
    #     """
    #     Gère le mode "Liste emplacement et article" pour tous les comptages.
        
    #     Args:
    #         warehouses: Liste des entrepôts à traiter
            
    #     Raises:
    #         InventoryValidationError: Si aucun stock n'est trouvé
    #     """
    #     if not self._check_stocks_exist(warehouses):
    #         warehouse_names = [w.warehouse_name for w in warehouses]
    #         logger.warning(f"Aucun stock trouvé pour les entrepôts: {', '.join(warehouse_names)}")
    #         raise InventoryValidationError(
    #             "Aucun stock trouvé pour les entrepôts de cet inventaire"
    #         )

    def launch_inventory(self, inventory_id: int) -> None:
        """
        Lance un inventaire en vérifiant le mode de comptage et en remplissant les détails si nécessaire.
        
        Args:
            inventory_id: L'ID de l'inventaire à lancer
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            InventoryValidationError: Si l'inventaire ne peut pas être lancé
        """
        try:
            # Récupérer l'inventaire
            inventory = self.repository.get_by_id(inventory_id)
            
            # Vérifier si l'inventaire est en attente
            if inventory.status != 'EN PREPARATION':
                raise InventoryValidationError(
                    "Seuls les inventaires en attente peuvent être lancés"
                )
            
            # Récupérer le premier comptage
            first_counting = inventory.countings.filter(order=1).first()
            if not first_counting:
                raise InventoryValidationError("Aucun comptage trouvé pour cet inventaire")
            
            # Récupérer les entrepôts de l'inventaire
            warehouses = [link.warehouse for link in inventory.awi_links.all()]
            
            # Si le premier comptage est en mode "Etat de stock"
            if first_counting.count_mode == "Etat de stock":
                self._handle_etat_stock_mode(first_counting, warehouses, inventory_id)
            
            # Vérifier tous les comptages pour le mode "Liste emplacement et article"
            # article_countings = inventory.countings.filter(count_mode="Liste emplacement et article")
            # if article_countings.exists():
            #     self._handle_liste_emplacement_article_mode(warehouses)
            
            # Si on arrive ici, soit le premier comptage est en mode "Etat de stock" et les stocks existent,
            # soit il y a des comptages en mode "Liste emplacement et article" et les stocks existent
            # On peut donc lancer l'inventaire
            inventory.status = 'EN REALISATION'
            inventory.en_realisation_status_date = timezone.now()
            inventory.save()
            
        except InventoryNotFoundError:
            raise
        except InventoryValidationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors du lancement de l'inventaire: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors du lancement de l'inventaire: {str(e)}")

    def cancel_inventory(self, inventory_id: int) -> None:
        """
        Annule le lancement d'un inventaire si son statut est 'LAUNCH'.
        Si le premier comptage est en mode 'Etat de stock', vide la table InventoryDetail.
        
        Args:
            inventory_id: L'ID de l'inventaire à annuler
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            InventoryValidationError: Si l'inventaire ne peut pas être annulé
        """
        try:
            # Récupérer l'inventaire
            inventory = self.repository.get_by_id(inventory_id)
            
            # Vérifier si l'inventaire est en statut LAUNCH
            if inventory.status != 'EN REALISATION':
                raise InventoryValidationError(
                    "Seuls les inventaires en statut 'EN REALISATION' peuvent être annulés"
                )
            
            # Récupérer le premier comptage
            first_counting = inventory.countings.filter(order=1).first()
            if not first_counting:
                raise InventoryValidationError("Aucun comptage trouvé pour cet inventaire")
            
            # Si le mode est "Etat de stock", vider la table InventoryDetail
            if first_counting.count_mode == "Etat de stock":
                CountingDetail.objects.filter(counting=first_counting).delete()
            
            # Mettre à jour le statut de l'inventaire
            inventory.status = 'EN PREPARATION'
            inventory.lunch_status_date = None
            inventory.save()
            
            # Note: Le comptage n'a plus de champ status, donc on ne met plus à jour le statut
            
        except InventoryNotFoundError:
            raise
        except InventoryValidationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de l'inventaire: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors de l'annulation de l'inventaire: {str(e)}")

    def get_warehouse_stats_for_inventory(self, inventory_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les statistiques des warehouses pour un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            List[Dict[str, Any]]: Liste des statistiques par warehouse
        """
        from django.db.models import Count, Q
        from ..models import Job, Assigment, Setting
        from apps.users.models import UserApp
        
        try:
            # Récupérer l'inventaire
            inventory = self.repository.get_by_id(inventory_id)
            if not inventory:
                raise InventoryNotFoundError(f"L'inventaire avec l'ID {inventory_id} n'existe pas.")
            
            # Récupérer tous les warehouses associés à cet inventaire
            warehouse_settings = Setting.objects.filter(
                inventory=inventory
            ).select_related('warehouse')
            
            stats = []
            
            for setting in warehouse_settings:
                warehouse = setting.warehouse
                
                # Compter les jobs pour ce warehouse et cet inventaire
                jobs_count = Job.objects.filter(
                    warehouse=warehouse,
                    inventory=inventory
                ).count()
                
                # Compter les équipes (sessions mobiles uniques) pour ce warehouse et cet inventaire
                teams_count = Assigment.objects.filter(
                    job__warehouse=warehouse,
                    job__inventory=inventory,
                    session__isnull=False,
                    session__type='Mobile'
                ).values('session').distinct().count()
                
                stats.append({
                    'warehouse_id': warehouse.id,
                    'warehouse_reference': warehouse.reference,
                    'warehouse_name': warehouse.warehouse_name,
                    'jobs_count': jobs_count,
                    'teams_count': teams_count
                })
            
            return stats
            
        except Exception as e:
            raise InventoryValidationError(f"Erreur lors de la récupération des statistiques: {str(e)}")

    def get_warehouse_jobs_sessions_count(self, inventory_id: int) -> List[Dict[str, Any]]:
        """
        Récupère le nom du warehouse avec le count des jobs et sessions associés
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            List[Dict[str, Any]]: Liste avec nom warehouse, count jobs et count sessions
        """
        try:
            # Vérifier que l'inventaire existe
            inventory = self.repository.get_by_id(inventory_id)
            if not inventory:
                raise InventoryNotFoundError(f"L'inventaire avec l'ID {inventory_id} n'existe pas.")
            
            # Utiliser le repository pour récupérer les statistiques
            return self.repository.get_warehouse_jobs_sessions_stats(inventory_id)
            
        except InventoryNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques warehouse: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors de la récupération des statistiques warehouse: {str(e)}")

    def validate_launch_inventory(self, inventory_id: int) -> Dict[str, Any]:
        """
        Valide le lancement d'un inventaire via le usecase métier.
        """
        validator = InventoryLaunchValidationUseCase()
        return validator.validate(inventory_id)

    def complete_inventory(self, inventory_id: int) -> Dict[str, Any]:
        """
        Marque un inventaire comme terminé si tous ses jobs sont terminés.
        
        Args:
            inventory_id: L'ID de l'inventaire à finaliser
            
        Returns:
            Dict[str, Any]: Dictionnaire contenant:
                - 'success': bool - True si l'inventaire a été finalisé, False sinon
                - 'inventory': Inventory - L'inventaire mis à jour (si success=True)
                - 'jobs_not_completed': List[Dict] - Liste des jobs non terminés (si success=False)
                - 'message': str - Message descriptif
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            InventoryValidationError: Si l'inventaire ne peut pas être finalisé (statut incorrect, aucun job)
        """
        from ..models import Job
        
        try:
            # Récupérer l'inventaire
            inventory = self.repository.get_by_id(inventory_id)
            
            # Vérifier que l'inventaire est en statut EN REALISATION
            if inventory.status != 'EN REALISATION':
                raise InventoryValidationError(
                    f"Seuls les inventaires en statut 'EN REALISATION' peuvent être finalisés. "
                    f"Statut actuel: {inventory.status}"
                )
            
            # Récupérer tous les jobs de cet inventaire
            jobs = Job.objects.filter(inventory_id=inventory_id)
            
            # Vérifier qu'il y a au moins un job
            if not jobs.exists():
                raise InventoryValidationError(
                    "Aucun job trouvé pour cet inventaire. Impossible de finaliser."
                )
            
            # Vérifier que tous les jobs sont terminés
            jobs_not_completed = jobs.exclude(status='TERMINE')
            
            if jobs_not_completed.exists():
                # Préparer la liste des jobs non terminés avec leurs informations
                jobs_not_completed_list = [
                    {
                        'id': job.id,
                        'reference': job.reference,
                        'status': job.status,
                        'warehouse_id': job.warehouse_id,
                        'warehouse_reference': job.warehouse.reference if job.warehouse else None,
                        'warehouse_name': job.warehouse.warehouse_name if job.warehouse else None,
                    }
                    for job in jobs_not_completed.select_related('warehouse')
                ]
                
                return {
                    'success': False,
                    'message': f"Impossible de finaliser l'inventaire. {len(jobs_not_completed)} job(s) non terminé(s).",
                    'jobs_not_completed': jobs_not_completed_list,
                    'total_jobs': jobs.count(),
                    'completed_jobs': jobs.filter(status='TERMINE').count(),
                    'inventory': None
                }
            
            # Si tous les jobs sont terminés, mettre à jour le statut de l'inventaire
            inventory = self.repository.update_status(inventory_id, 'TERMINE')
            
            logger.info(
                f"Inventaire {inventory.reference} (ID: {inventory_id}) marqué comme terminé. "
                f"Nombre total de jobs: {jobs.count()}"
            )
            
            return {
                'success': True,
                'message': "L'inventaire a été marqué comme terminé avec succès",
                'jobs_not_completed': [],
                'total_jobs': jobs.count(),
                'completed_jobs': jobs.count(),
                'inventory': inventory
            }
            
        except InventoryNotFoundError:
            raise
        except InventoryValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Erreur lors de la finalisation de l'inventaire {inventory_id}: {str(e)}", 
                exc_info=True
            )
            raise InventoryValidationError(
                f"Erreur lors de la finalisation de l'inventaire: {str(e)}"
            )

    def close_inventory(self, inventory_id: int) -> Inventory:
        """
        Marque un inventaire comme clôturé si celui-ci est déjà terminé.
        
        Args:
            inventory_id: L'ID de l'inventaire à clôturer
            
        Returns:
            Inventory: L'inventaire mis à jour
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            InventoryValidationError: Si l'inventaire n'est pas terminé ou ne peut pas être clôturé
        """
        try:
            # Récupérer l'inventaire
            inventory = self.repository.get_by_id(inventory_id)
            
            # Vérifier que l'inventaire est en statut TERMINE
            if inventory.status != 'TERMINE':
                raise InventoryValidationError(
                    f"Seuls les inventaires en statut 'TERMINE' peuvent être clôturés. "
                    f"Statut actuel: {inventory.status}"
                )
            
            # Si l'inventaire est terminé, mettre à jour le statut à CLOTURE
            inventory = self.repository.update_status(inventory_id, 'CLOTURE')
            
            logger.info(
                f"Inventaire {inventory.reference} (ID: {inventory_id}) marqué comme clôturé."
            )
            
            return inventory
            
        except InventoryNotFoundError:
            raise
        except InventoryValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Erreur lors de la clôture de l'inventaire {inventory_id}: {str(e)}", 
                exc_info=True
            )
            raise InventoryValidationError(
                f"Erreur lors de la clôture de l'inventaire: {str(e)}"
            )

    