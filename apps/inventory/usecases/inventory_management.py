"""
Use case générique pour la gestion d'inventaire (création et mise à jour).
"""
from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import transaction
from ..models import Inventory, Setting, Counting
from ..exceptions import InventoryValidationError, InventoryNotFoundError
from ..repositories.inventory_repository import InventoryRepository
from .counting_dispatcher import CountingDispatcher
from apps.masterdata.models import Account, Warehouse
import logging

logger = logging.getLogger(__name__)

class InventoryManagementUseCase:
    """
    Use case générique pour la gestion d'inventaire avec validation métier.
    
    Ce use case permet de créer ou mettre à jour un inventaire en 3 étapes distinctes :
    1. Validation des données
    2. Création/Mise à jour de l'inventaire et des settings
    3. Création/Mise à jour des comptages liés à l'inventaire
    
    Exemples d'utilisation :
    
    # Création complète en une fois
    use_case = InventoryManagementUseCase()
    result = use_case.create(data)
    
    # Mise à jour complète en une fois
    result = use_case.update(inventory_id, data)
    
    # Validation uniquement
    validation_result = use_case.validate_only(data)
    
    # Exécution étape par étape
    use_case.step1_validate_data(data)
    inventory = use_case.step2_manage_inventory_and_settings(inventory_id, data)
    countings = use_case.step3_manage_countings(inventory, data['comptages'])
    """
    
    def __init__(self, inventory_repository: InventoryRepository = None, counting_dispatcher: CountingDispatcher = None):
        self.inventory_repository = inventory_repository or InventoryRepository()
        self.counting_dispatcher = counting_dispatcher or CountingDispatcher()
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute la création d'inventaire avec validation complète en 3 étapes.
        
        Args:
            data: Données de l'inventaire au format JSON
            
        Returns:
            Dict[str, Any]: Résultat de la création
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        try:
            with transaction.atomic():
                # ÉTAPE 1: Validation des données
                self.step1_validate_data(data)
                
                # ÉTAPE 2: Création de l'inventaire et des settings
                inventory = self.step2_manage_inventory_and_settings(None, data)
                
                # ÉTAPE 3: Création des comptages liés à l'inventaire créé
                countings = self.step3_manage_countings(inventory, data['comptages'])
                
                # Retour du résultat formaté
                return self._format_response(inventory, countings, "créé")
                
        except Exception as e:
            logger.error(f"Erreur dans InventoryManagementUseCase.create: {str(e)}", exc_info=True)
            raise
    
    def update(self, inventory_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute la mise à jour d'inventaire avec validation complète en 3 étapes.
        
        Args:
            inventory_id: L'ID de l'inventaire à mettre à jour
            data: Données de l'inventaire au format JSON
            
        Returns:
            Dict[str, Any]: Résultat de la mise à jour
            
        Raises:
            InventoryValidationError: Si les données sont invalides
            InventoryNotFoundError: Si l'inventaire n'existe pas
        """
        try:
            with transaction.atomic():
                # Vérifier que l'inventaire existe
                inventory = self.inventory_repository.get_by_id(inventory_id)
                
                # ÉTAPE 1: Validation des données
                self.step1_validate_data(data)
                
                # ÉTAPE 2: Mise à jour de l'inventaire et des settings
                inventory = self.step2_manage_inventory_and_settings(inventory_id, data)
                
                # ÉTAPE 3: Mise à jour des comptages liés à l'inventaire
                countings = self.step3_manage_countings(inventory, data.get('comptages', []))
                
                # Retour du résultat formaté
                return self._format_response(inventory, countings, "mis à jour")
                
        except InventoryNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erreur dans InventoryManagementUseCase.update: {str(e)}", exc_info=True)
            raise
    
    def step1_validate_data(self, data: Dict[str, Any]) -> None:
        """
        Étape 1: Validation complète des données.
        
        Args:
            data: Données de l'inventaire au format JSON
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        self._validate_input_data(data)
        self._validate_entities(data)
        if data.get('comptages'):
            self._validate_countings(data['comptages'])
    
    def step2_manage_inventory_and_settings(self, inventory_id: Optional[int], data: Dict[str, Any]) -> Inventory:
        """
        Étape 2: Création ou mise à jour de l'inventaire et des settings.
        
        Args:
            inventory_id: L'ID de l'inventaire (None pour création)
            data: Données de l'inventaire au format JSON
            
        Returns:
            Inventory: L'inventaire créé ou mis à jour
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        if inventory_id is None:
            return self._create_inventory_and_settings(data)
        else:
            return self._update_inventory_and_settings(inventory_id, data)
    
    def step3_manage_countings(self, inventory: Inventory, comptages: List[Dict[str, Any]]) -> List[Counting]:
        """
        Étape 3: Création ou mise à jour des comptages liés à l'inventaire.
        
        Args:
            inventory: L'inventaire
            comptages: Liste des données des comptages
            
        Returns:
            List[Counting]: Liste des comptages créés ou mis à jour
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        if comptages:
            # Supprimer les anciens comptages et en créer de nouveaux
            Counting.objects.filter(inventory=inventory).delete()
            return self._create_countings_for_inventory(inventory, comptages)
        return []
    
    def _create_inventory_and_settings(self, data: Dict[str, Any]) -> Inventory:
        """
        Crée l'inventaire et les settings associés.
        
        Args:
            data: Données de l'inventaire
            
        Returns:
            Inventory: L'inventaire créé
        """
        from django.utils import timezone
        
        # Créer l'objet Inventory sans sauvegarder
        inventory = Inventory(
            label=data['label'],
            date=data['date'],
            status='EN PREPARATION',
            inventory_type=data.get('inventory_type', 'GENERAL'),
            en_preparation_status_date=timezone.now()  # Définir la date de préparation
        )
        
        # Générer la référence manuellement
        inventory.reference = inventory.generate_reference(inventory.REFERENCE_PREFIX)
        
        # Sauvegarder l'objet
        inventory.save()
        
        # Création des settings (liens entre inventaire, entrepôts et compte)
        account_id = data['account_id']
        for warehouse_info in data['warehouse']:
            warehouse_id = warehouse_info['id']
            
            # Créer l'objet Setting sans sauvegarder
            setting = Setting(
                inventory=inventory,
                warehouse_id=warehouse_id,
                account_id=account_id
            )
            
            # Générer la référence manuellement
            setting.reference = setting.generate_reference(setting.REFERENCE_PREFIX)
            
            # Sauvegarder l'objet
            setting.save()
        
        logger.info(f"Inventaire {inventory.id} créé avec {len(data['warehouse'])} entrepôts")
        return inventory
    
    def _update_inventory_and_settings(self, inventory_id: int, data: Dict[str, Any]) -> Inventory:
        """
        Met à jour l'inventaire et les settings associés.
        
        Args:
            inventory_id: L'ID de l'inventaire à mettre à jour
            data: Données de l'inventaire
            
        Returns:
            Inventory: L'inventaire mis à jour
        """
        # Récupération de l'inventaire
        inventory = self.inventory_repository.get_by_id(inventory_id)
        
        # Mise à jour des champs de l'inventaire
        if 'label' in data:
            inventory.label = data['label']
        if 'date' in data:
            inventory.date = data['date']
        if 'inventory_type' in data:
            inventory.inventory_type = data['inventory_type']
        
        inventory.save()
        
        # Mise à jour des settings si fournis
        if 'account_id' in data and 'warehouse' in data:
            # Suppression des anciens settings
            Setting.objects.filter(inventory=inventory).delete()
            
            # Création des nouveaux settings
            account_id = data['account_id']
            for warehouse_info in data['warehouse']:
                warehouse_id = warehouse_info['id']
                
                # Créer l'objet Setting sans sauvegarder
                setting = Setting(
                    inventory=inventory,
                    warehouse_id=warehouse_id,
                    account_id=account_id
                )
                
                # Générer la référence manuellement
                setting.reference = setting.generate_reference(setting.REFERENCE_PREFIX)
                
                # Sauvegarder l'objet
                setting.save()
        
        logger.info(f"Inventaire {inventory.id} mis à jour")
        return inventory
    
    def _create_countings_for_inventory(self, inventory: Inventory, comptages: List[Dict[str, Any]]) -> List[Counting]:
        """
        Crée les comptages liés à l'inventaire.
        
        Args:
            inventory: L'inventaire
            comptages: Liste des données des comptages
            
        Returns:
            List[Counting]: Liste des comptages créés
        """
        countings = []
        
        for comptage_data in comptages:
            # Ajouter l'ID de l'inventaire aux données du comptage
            comptage_data['inventory_id'] = inventory.id
            
            # Obtenir le use case approprié via le dispatcher
            temp_counting = Counting(
                count_mode=comptage_data['count_mode'],
                unit_scanned=comptage_data.get('unit_scanned', False),
                entry_quantity=comptage_data.get('entry_quantity', False),
                is_variant=comptage_data.get('is_variant', False),
                n_lot=comptage_data.get('n_lot', False),
                n_serie=comptage_data.get('n_serie', False),
                dlc=comptage_data.get('dlc', False),
                show_product=comptage_data.get('show_product', False),
                stock_situation=comptage_data.get('stock_situation', False),
                quantity_show=comptage_data.get('quantity_show', False)
            )
            
            use_case = self.counting_dispatcher.get_use_case_for_counting(temp_counting)
            
            # Créer le comptage via le use case approprié
            counting = use_case.create_counting(comptage_data)
            countings.append(counting)
            
            logger.info(f"Comptage {counting.id} créé pour l'inventaire {inventory.id} (mode: {counting.count_mode})")
        
        return countings
    
    def _validate_input_data(self, data: Dict[str, Any]) -> None:
        """
        Valide les données d'entrée.
        """
        errors = []
        
        # Validation des champs obligatoires pour la création
        if not data.get('label'):
            errors.append("Le label est obligatoire")
        
        if not data.get('date'):
            errors.append("La date est obligatoire")
        
        if not data.get('account_id'):
            errors.append("L'account_id est obligatoire")
        
        if not data.get('warehouse'):
            errors.append("Au moins un entrepôt est obligatoire")
        elif not isinstance(data['warehouse'], list) or len(data['warehouse']) == 0:
            errors.append("La liste des entrepôts ne peut pas être vide")
        
        if errors:
            raise InventoryValidationError(" | ".join(errors))
    
    def _validate_entities(self, data: Dict[str, Any]) -> None:
        """
        Valide l'existence des entités référencées.
        """
        errors = []
        
        # Validation du compte
        try:
            Account.objects.get(id=data['account_id'])
        except Account.DoesNotExist:
            errors.append(f"Le compte avec l'ID {data['account_id']} n'existe pas")
        
        # Validation des entrepôts
        warehouses = data.get('warehouse', [])
        
        if warehouses:
            for warehouse_info in warehouses:
                warehouse_id = warehouse_info.get('id')
                if not warehouse_id:
                    errors.append("Chaque entrepôt doit avoir un ID")
                    continue
                
                try:
                    Warehouse.objects.get(id=warehouse_id)
                except Warehouse.DoesNotExist:
                    errors.append(f"L'entrepôt avec l'ID {warehouse_id} n'existe pas")
        
        if errors:
            raise InventoryValidationError(" | ".join(errors))
    
    def _validate_countings(self, comptages: List[Dict[str, Any]]) -> None:
        """
        Valide les comptages selon les règles métier spécifiques.
        """
        errors = []
        
        # Vérifier qu'il y a exactement 3 comptages
        if len(comptages) != 3:
            errors.append("Un inventaire doit contenir exactement 3 comptages")
            if errors:
                raise InventoryValidationError(" | ".join(errors))
        
        # Trier les comptages par ordre
        comptages_sorted = sorted(comptages, key=lambda x: x.get('order', 0))
        
        # Vérifier que les ordres sont 1, 2, 3
        orders = [c.get('order') for c in comptages_sorted]
        if orders != [1, 2, 3]:
            errors.append("Les comptages doivent avoir les ordres 1, 2, 3")
        
        # Récupérer les modes de comptage par ordre
        count_modes = [c.get('count_mode') for c in comptages_sorted]
        
        # Vérifier que tous les modes sont valides
        valid_modes = ['en vrac', 'par article', 'image de stock']
        for i, mode in enumerate(count_modes):
            if mode not in valid_modes:
                errors.append(f"Comptage {i+1}: Mode de comptage invalide '{mode}'")
        
        # Validation des combinaisons autorisées
        first_mode = count_modes[0]
        second_mode = count_modes[1]
        third_mode = count_modes[2]
        article_param_fields = ['n_lot', 'dlc', 'n_serie']
        
        # Scénario 1: Premier comptage = "image de stock"
        if first_mode == "image de stock":
            # Les 2e et 3e comptages doivent être du même mode (soit "en vrac", soit "par article")
            if second_mode != third_mode:
                errors.append("Si le premier comptage est 'image de stock', les 2e et 3e comptages doivent avoir le même mode")
            
            if second_mode not in ["en vrac", "par article"]:
                errors.append("Si le premier comptage est 'image de stock', les 2e et 3e comptages doivent être 'en vrac' ou 'par article'")

            # Vérifier l'alignement des paramètres si les comptages 2 et 3 sont "par article"
            if second_mode == "par article":
                first_params = {field: bool(comptages_sorted[0].get(field, False)) for field in article_param_fields}
                second_params = {field: bool(comptages_sorted[1].get(field, False)) for field in article_param_fields}
                third_params = {field: bool(comptages_sorted[2].get(field, False)) for field in article_param_fields}

                if second_params != third_params:
                    errors.append(
                        "Les comptages 2 et 3 en mode 'par article' doivent partager les mêmes paramètres (N° lot, DLC, N° série)"
                    )
                if second_params != first_params or third_params != first_params:
                    errors.append(
                        "Si le premier comptage est 'image de stock', les paramètres 'par article' sélectionnés (N° lot, DLC, N° série) doivent rester identiques sur les 2e et 3e comptages"
                    )
        
        # Scénario 2: Premier comptage = "en vrac" ou "par article"
        elif first_mode in ["en vrac", "par article"]:
            # Tous les comptages doivent être "en vrac" ou "par article"
            for i, mode in enumerate(count_modes):
                if mode not in ["en vrac", "par article"]:
                    errors.append(f"Si le premier comptage n'est pas 'image de stock', tous les comptages doivent être 'en vrac' ou 'par article' (comptage {i+1}: '{mode}')")

            if first_mode == "en vrac":
                # Imposer le même mode "en vrac" pour les 2e et 3e comptages
                if second_mode != "en vrac" or third_mode != "en vrac":
                    errors.append("Si le premier comptage est 'en vrac', les 2e et 3e comptages doivent également être 'en vrac'")

            if first_mode == "par article":
                # Imposer le mode "par article" et l'alignement des paramètres pour les 2e et 3e comptages
                if second_mode != "par article" or third_mode != "par article":
                    errors.append("Si le premier comptage est 'par article', les 2e et 3e comptages doivent également être 'par article'")
                else:
                    first_params = {field: bool(comptages_sorted[0].get(field, False)) for field in article_param_fields}

                    for index, counting in enumerate(comptages_sorted[1:], start=2):
                        counting_params = {field: bool(counting.get(field, False)) for field in article_param_fields}
                        if counting_params != first_params:
                            order_value = counting.get('order', index)
                            differing_fields = [
                                label for label in article_param_fields if counting_params[label] != first_params[label]
                            ]
                            formatted_fields = ", ".join(differing_fields)
                            errors.append(
                                f"Comptage {order_value}: Les paramètres ({formatted_fields}) doivent être identiques au premier comptage 'par article'"
                            )
        
        # Validation des champs obligatoires et spécifiques via CountingDispatcher
        for i, comptage in enumerate(comptages_sorted, 1):
            # Validation des champs obligatoires
            if not comptage.get('order'):
                errors.append(f"Comptage {i}: L'ordre est obligatoire")
            
            if not comptage.get('count_mode'):
                errors.append(f"Comptage {i}: Le mode de comptage est obligatoire")
            
            # Validation spécifique via CountingDispatcher
            count_mode = comptage.get('count_mode')
            if count_mode:
                try:
                    # Valider via le dispatcher
                    self.counting_dispatcher.validate_counting_data(comptage)
                except Exception as e:
                    errors.append(f"Comptage {i}: {str(e)}")
        
        if errors:
            raise InventoryValidationError(" | ".join(errors))
    
    def _format_response(self, inventory: Inventory, countings: List[Counting], action: str) -> Dict[str, Any]:
        """
        Formate la réponse de création ou mise à jour.
        """
        return {
            "success": True,
            "message": f"Inventaire {action} avec succès"
        }
    
    def validate_only(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide uniquement les données sans créer ou mettre à jour l'inventaire.
        
        Args:
            data: Données de l'inventaire au format JSON
            
        Returns:
            Dict[str, Any]: Résultat de la validation
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        try:
            # ÉTAPE 1: Validation des données
            self._validate_input_data(data)
            self._validate_entities(data)
            if data.get('comptages'):
                self._validate_countings(data['comptages'])
            
            return {
                "success": True,
                "message": "Données validées avec succès"
            }
            
        except Exception as e:
            logger.error(f"Erreur de validation dans InventoryManagementUseCase: {str(e)}", exc_info=True)
            raise 