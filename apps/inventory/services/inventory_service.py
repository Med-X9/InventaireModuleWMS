"""
Service pour la gestion des inventaires.
"""
from typing import Dict, Any, List
from django.utils import timezone
from ..interfaces.inventory_interface import IInventoryRepository
from ..repositories import InventoryRepository
from ..exceptions import InventoryValidationError, InventoryNotFoundError
from ..models import Inventory, Setting, Counting, InventoryDetail
from django.db import IntegrityError
import logging
from .counting_service import CountingService
from apps.masterdata.models import Warehouse

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
        valid_modes = ['Liste d\'emplacement', 'Liste emplacement et article']
        for i, comptage in enumerate(comptages, 1):
            if comptage.get('count_mode') not in valid_modes:
                errors.append(f"Mode de comptage invalide pour le comptage {i}")
        return errors
    
    def create_inventory(self, data: Dict[str, Any]) -> Inventory:
        """
        Crée un nouvel inventaire.
        
        Args:
            data: Les données de l'inventaire
            
        Returns:
            Inventory: L'inventaire créé
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        # Validation complète des données avant toute création
        self.validate_inventory_data(data)
        
        # Extraction des données
        label = data['label']
        date = data['date']
        account_id = data['account']
        warehouse_ids = data['warehouse']
        comptages_data = data['comptages']
        
        try:
            # Création de l'inventaire avec les champs status et pending_status_date
            inventory = Inventory.objects.create(
                label=label,
                date=date,
                status='PENDING',
                pending_status_date=timezone.now()
            )
            
            # Création des liens entre l'inventaire et les entrepôts
            for warehouse_id in warehouse_ids:
                Setting.objects.create(
                    account_id=account_id,
                    warehouse_id=warehouse_id,
                    inventory=inventory
                )
            
            # Création des comptages via le service de comptage
            self.counting_service.create_countings(inventory.id, comptages_data)
            
            return inventory
            
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
            
            if inventory.status != 'PENDING':
                raise InventoryValidationError(
                    "Seuls les inventaires en attente peuvent être supprimés"
                )
            
            # Soft delete de l'inventaire
            inventory.soft_delete()
            
            # Soft delete des entités associées
            # Soft delete des settings
            for setting in inventory.awi_links.all():
                setting.soft_delete()
            
            # Soft delete des comptages
            for counting in inventory.countings.all():
                counting.soft_delete()
            
            # Soft delete des PDAs
            for pda in inventory.pdas.all():
                pda.soft_delete()
            
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

    def update_inventory(self, inventory_id: int, data: Dict[str, Any]) -> Inventory:
        """
        Met à jour un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire à mettre à jour
            data: Les nouvelles données de l'inventaire
            
        Returns:
            Inventory: L'inventaire mis à jour
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            InventoryValidationError: Si les données sont invalides
        """
        try:
            # Récupération de l'inventaire
            inventory = self.get_inventory_by_id(inventory_id)
            
            # Préparation des données pour la validation
            validation_data = {
                'label': data.get('label'),
                'date': data.get('date'),
                'account': data.get('account_id'),
                'warehouse': data.get('warehouse_ids'),
                'comptages': data.get('comptages', [])
            }
            
            # Validation des données
            self.validate_inventory_data(validation_data)
            
            # Extraction des données
            label = data['label']
            date = data['date']
            account_id = data['account_id']
            warehouse_ids = data['warehouse_ids']
            comptages_data = data['comptages']
            
            # Mise à jour de l'inventaire
            inventory.label = label
            inventory.date = date
            inventory.save()
            
            # Suppression des anciens paramètres
            Setting.objects.filter(inventory=inventory).delete()
            
            # Création des nouveaux paramètres
            for warehouse_id in warehouse_ids:
                Setting.objects.create(
                    account_id=account_id,
                    warehouse_id=warehouse_id,
                    inventory=inventory
                )
            
            # Suppression des anciens comptages
            Counting.objects.filter(inventory=inventory).delete()
            
            # Création des nouveaux comptages
            for comptage_data in comptages_data:
                Counting.objects.create(
                    inventory=inventory,
                    **comptage_data
                )
            
            return inventory
            
        except InventoryNotFoundError:
            raise
        except InventoryValidationError:
            raise
        except IntegrityError as e:
            logger.error(f"Erreur d'intégrité lors de la mise à jour de l'inventaire: {str(e)}")
            raise InventoryValidationError("Erreur de validation des données")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la mise à jour de l'inventaire: {str(e)}")
            raise InventoryValidationError(str(e))

    def _check_stocks_exist(self, warehouses: List[Warehouse]) -> bool:
        """
        Vérifie si des stocks existent pour les entrepôts donnés.
        
        Args:
            warehouses: Liste des entrepôts à vérifier
            
        Returns:
            bool: True si des stocks existent, False sinon
        """
        from apps.masterdata.models import Stock
        
        for warehouse in warehouses:
            stocks_count = Stock.objects.filter(
                location__sous_zone__zone__warehouse=warehouse,
                location__is_active=True,
                location__sous_zone__zone__zone_status='ACTIVE',
                is_deleted=False
            ).count()
            
            logger.info(f"Nombre de stocks trouvés pour l'entrepôt {warehouse.warehouse_name}: {stocks_count}")
            
            if stocks_count > 0:
                return True
        return False

    def _create_inventory_details_from_stocks(self, counting: Counting, warehouses: List[Warehouse]) -> None:
        """
        Crée les détails d'inventaire à partir des stocks existants.
        
        Args:
            counting: Le comptage pour lequel créer les détails
            warehouses: Liste des entrepôts à traiter
        """
        from apps.masterdata.models import Stock
        
        for warehouse in warehouses:
            stocks = Stock.objects.filter(
                location__sous_zone__zone__warehouse=warehouse,
                location__is_active=True,
                location__sous_zone__zone__zone_status='ACTIVE',
                is_deleted=False
            ).select_related('product', 'location', 'location__sous_zone', 'location__sous_zone__zone')
            
            stocks_count = stocks.count()
            logger.info(f"Création de {stocks_count} détails d'inventaire pour l'entrepôt {warehouse.warehouse_name}")
            
            for stock in stocks:
                quantity = int(stock.quantity_available)
                InventoryDetail.objects.create(
                    counting=counting,
                    product=stock.product,
                    location=stock.location,
                    quantity_inventoried=quantity
                )

    def _handle_etat_stock_mode(self, first_counting: Counting, warehouses: List[Warehouse]) -> None:
        """
        Gère le mode "Etat de stock" pour le premier comptage.
        
        Args:
            first_counting: Le premier comptage
            warehouses: Liste des entrepôts à traiter
            
        Raises:
            InventoryValidationError: Si aucun stock n'est trouvé
        """
        if not self._check_stocks_exist(warehouses):
            warehouse_names = [w.warehouse_name for w in warehouses]
            logger.warning(f"Aucun stock trouvé pour les entrepôts: {', '.join(warehouse_names)}")
            raise InventoryValidationError(
                "Aucun stock trouvé pour les entrepôts de cet inventaire"
            )
        
        self._create_inventory_details_from_stocks(first_counting, warehouses)
        
        # Mettre à jour le statut du premier comptage en END
        first_counting.status = 'END'
        first_counting.date_status_end = timezone.now()
        first_counting.save()

    def _handle_liste_emplacement_article_mode(self, warehouses: List[Warehouse]) -> None:
        """
        Gère le mode "Liste emplacement et article" pour tous les comptages.
        
        Args:
            warehouses: Liste des entrepôts à traiter
            
        Raises:
            InventoryValidationError: Si aucun stock n'est trouvé
        """
        if not self._check_stocks_exist(warehouses):
            warehouse_names = [w.warehouse_name for w in warehouses]
            logger.warning(f"Aucun stock trouvé pour les entrepôts: {', '.join(warehouse_names)}")
            raise InventoryValidationError(
                "Aucun stock trouvé pour les entrepôts de cet inventaire"
            )

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
            if inventory.status != 'PENDING':
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
                self._handle_etat_stock_mode(first_counting, warehouses)
            
            # Vérifier tous les comptages pour le mode "Liste emplacement et article"
            article_countings = inventory.countings.filter(count_mode="Liste emplacement et article")
            if article_countings.exists():
                self._handle_liste_emplacement_article_mode(warehouses)
            
            # Si on arrive ici, soit le premier comptage est en mode "Etat de stock" et les stocks existent,
            # soit il y a des comptages en mode "Liste emplacement et article" et les stocks existent
            # On peut donc lancer l'inventaire
            inventory.status = 'LAUNCH'
            inventory.lunch_status_date = timezone.now()
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
            if inventory.status != 'LAUNCH':
                raise InventoryValidationError(
                    "Seuls les inventaires en statut 'LAUNCH' peuvent être annulés"
                )
            
            # Récupérer le premier comptage
            first_counting = inventory.countings.filter(order=1).first()
            if not first_counting:
                raise InventoryValidationError("Aucun comptage trouvé pour cet inventaire")
            
            # Si le mode est "Etat de stock", vider la table InventoryDetail
            if first_counting.count_mode == "Etat de stock":
                InventoryDetail.objects.filter(counting=first_counting).delete()
            
            # Mettre à jour le statut de l'inventaire
            inventory.status = 'PENDING'
            inventory.lunch_status_date = None
            inventory.save()
            
            # Mettre à jour le statut du premier comptage
            first_counting.status = 'PENDING'
            first_counting.date_status_lunch = None
            first_counting.save()
            
        except InventoryNotFoundError:
            raise
        except InventoryValidationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de l'inventaire: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors de l'annulation de l'inventaire: {str(e)}") 