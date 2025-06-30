"""
Service pour la gestion des inventaires.
"""
from typing import Dict, Any, List
from django.utils import timezone
from ..repositories import InventoryRepository
from ..exceptions import InventoryValidationError, InventoryNotFoundError
from ..models import Inventory,  Counting, CountingDetail
import logging
from .counting_service import CountingService
from apps.masterdata.models import Warehouse
from ..interfaces.inventory_interface import IInventoryService

# Configuration du logger
logger = logging.getLogger(__name__)

class InventoryService(IInventoryService):
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
    
    def create_inventory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouvel inventaire en utilisant le use case.
        
        Args:
            data: Les données de l'inventaire
            
        Returns:
            Dict[str, Any]: Résultat de la création
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        try:
            # Utilisation du use case unifié pour la création
            from ..usecases.inventory_usecase import InventoryUseCase
            use_case = InventoryUseCase()
            result = use_case.create_inventory(data)
            
            # Ajouter le message spécifique à la création
            result['message'] = "Inventaire créé avec succès"
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'inventaire: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors de la création de l'inventaire: {str(e)}")

    def delete_inventory(self, inventory_id: int) -> None:
        """
        Supprime complètement un inventaire et tous ses enregistrements liés si son statut est en préparation.
        
        Args:
            inventory_id: L'ID de l'inventaire à supprimer
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            InventoryValidationError: Si l'inventaire ne peut pas être supprimé
        """
        try:
            inventory = self.repository.get_by_id(inventory_id)
            
            if inventory.status != 'EN PREPARATION':
                raise InventoryValidationError(
                    "Seuls les inventaires en préparation peuvent être supprimés"
                )
            
            # Suppression en cascade de tous les enregistrements liés
            
            # 1. Supprimer les CountingDetail liés aux comptages de cet inventaire
            from ..models import CountingDetail
            countings = inventory.countings.all()
            for counting in countings:
                CountingDetail.objects.filter(counting=counting).delete()
            
            # 2. Supprimer les comptages (Counting)
            inventory.countings.all().delete()
            
            # 3. Supprimer les settings (Setting)
            inventory.awi_links.all().delete()
            
            # 4. Supprimer les jobs liés à cet inventaire
            from ..models import Job
            Job.objects.filter(inventory=inventory).delete()
            
            # 5. Supprimer les écarts de comptage
            from ..models import EcartComptage
            EcartComptage.objects.filter(inventory=inventory).delete()
            
            # 6. Supprimer les ressources d'inventaire
            from ..models import InventoryDetailRessource
            InventoryDetailRessource.objects.filter(inventory=inventory).delete()
            
            # 7. Supprimer les planifications
            from ..models import Planning
            Planning.objects.filter(inventory=inventory).delete()
            
            # 8. Enfin, supprimer l'inventaire lui-même
            inventory.delete()
            
            logger.info(f"Inventaire {inventory_id} et tous ses enregistrements liés supprimés avec succès")
            
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

    def update_inventory(self, inventory_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un inventaire en utilisant le use case.
        
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
            # Utilisation du use case unifié pour la mise à jour
            from ..usecases.inventory_usecase import InventoryUseCase
            use_case = InventoryUseCase()
            result = use_case.update_inventory(inventory_id, data)
            
            # Ajouter le message spécifique à la mise à jour
            result['message'] = "Inventaire mis à jour avec succès"
            return result
            
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
        
        # Mettre à jour le statut du premier comptage en END
        first_counting.status = 'END'
        first_counting.date_status_end = timezone.now()
        first_counting.save()

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
            
            # Vérifier si l'inventaire est en préparation
            if inventory.status != 'EN PREPARATION':
                raise InventoryValidationError(
                    "Seuls les inventaires en préparation peuvent être lancés"
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
            inventory.en_preparation_status_date = timezone.now()
            inventory.save()
            
        except InventoryNotFoundError:
            raise
        except InventoryValidationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de l'inventaire: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors de l'annulation de l'inventaire: {str(e)}")

    def get_inventory_list(self, filters_dict: Dict[str, Any] = None, ordering: str = '-date', page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Récupère la liste des inventaires avec filtres, tri et pagination.
        
        Args:
            filters_dict: Dictionnaire des filtres à appliquer
            ordering: Champ de tri (ex: '-date', 'label')
            page: Numéro de page
            page_size: Taille de page
            
        Returns:
            Dict[str, Any]: Résultat paginé avec les inventaires
        """
        try:
            # Récupérer le queryset filtré via le repository
            queryset = self.repository.get_by_filters(filters_dict or {})
            
            # Appliquer le tri
            if ordering:
                if ordering.startswith('-'):
                    field = ordering[1:]
                    queryset = queryset.order_by(f'-{field}')
                else:
                    queryset = queryset.order_by(ordering)
            
            # Appliquer la pagination
            from django.core.paginator import Paginator
            paginator = Paginator(queryset, page_size)
            
            try:
                page_obj = paginator.page(page)
            except:
                page_obj = paginator.page(1)
            
            # Sérialiser les résultats
            from ..serializers.inventory_serializer import InventoryDetailSerializer
            serializer = InventoryDetailSerializer(page_obj.object_list, many=True)
            
            return {
                "success": True,
                "message": "Liste des inventaires récupérée avec succès",
                "data": serializer.data,
                "pagination": {
                    "count": paginator.count,
                    "num_pages": paginator.num_pages,
                    "current_page": page_obj.number,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous(),
                    "next_page_number": page_obj.next_page_number() if page_obj.has_next() else None,
                    "previous_page_number": page_obj.previous_page_number() if page_obj.has_previous() else None,
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des inventaires: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors de la récupération de la liste des inventaires: {str(e)}")

    def get_inventory_detail(self, inventory_id: int) -> Inventory:
        """
        Récupère un inventaire avec toutes ses données associées.
        
        Args:
            inventory_id: L'ID de l'inventaire à récupérer
            
        Returns:
            Inventory: L'inventaire trouvé avec ses données associées
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
        """
        try:
            return self.repository.get_with_related_data(inventory_id)
        except Inventory.DoesNotExist:
            logger.error(f"Inventaire non trouvé avec l'ID: {inventory_id}")
            raise InventoryNotFoundError("L'inventaire demandé n'existe pas")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'inventaire: {str(e)}", exc_info=True)
            raise InventoryNotFoundError(f"Erreur lors de la récupération de l'inventaire: {str(e)}")

    def soft_delete_inventory(self, inventory_id: int) -> None:
        """
        Effectue un soft delete d'un inventaire si son statut est en préparation.
        
        Args:
            inventory_id: L'ID de l'inventaire à soft delete
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            InventoryValidationError: Si l'inventaire ne peut pas être soft delete
        """
        try:
            inventory = self.repository.get_by_id(inventory_id)
            
            if inventory.status != 'EN PREPARATION':
                raise InventoryValidationError(
                    "Seuls les inventaires en préparation peuvent être supprimés"
                )
            
            # Soft delete de l'inventaire (marquer comme supprimé sans supprimer physiquement)
            inventory.is_deleted = True
            inventory.deleted_at = timezone.now()
            inventory.save()
            
            logger.info(f"Inventaire {inventory_id} supprimés avec succès")
            
        except InventoryNotFoundError:
            raise
        except InventoryValidationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors du soft delete de l'inventaire: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors du supprimés de l'inventaire: {str(e)}")

    def restore_inventory(self, inventory_id: int) -> None:
        """
        Restaure un inventaire qui a été soft delete.
        
        Args:
            inventory_id: L'ID de l'inventaire à restaurer
            
        Raises:
            InventoryNotFoundError: Si l'inventaire n'existe pas
            InventoryValidationError: Si l'inventaire ne peut pas être restauré
        """
        try:
            # Utiliser directement la méthode restore du repository
            # qui gère le cas où l'inventaire n'est pas supprimé
            inventory = self.repository.restore(inventory_id)
            
            logger.info(f"Inventaire {inventory_id} restauré avec succès")
            
        except InventoryNotFoundError:
            raise
        except InventoryValidationError:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la restauration de l'inventaire: {str(e)}", exc_info=True)
            raise InventoryValidationError(f"Erreur lors de la restauration de l'inventaire: {str(e)}")

    def get_inventory_queryset(self, filters_dict: Dict[str, Any] = None, ordering: str = '-date'):
        """
        Retourne un queryset filtré et trié des inventaires, compatible avec la pagination DRF.
        """
        queryset = self.repository.get_by_filters(filters_dict or {})
        if ordering:
            if ordering.startswith('-'):
                field = ordering[1:]
                queryset = queryset.order_by(f'-{field}')
            else:
                queryset = queryset.order_by(ordering)
        return queryset

    