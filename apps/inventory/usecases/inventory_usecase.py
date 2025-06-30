"""
Use case pour la gestion d'inventaire (création et mise à jour).
"""
from typing import Dict, Any, List
from django.utils import timezone
from django.db import transaction
from ..models import Inventory, Setting, Counting
from ..exceptions import InventoryValidationError
from ..repositories.inventory_repository import InventoryRepository
from ..interfaces.inventory_use_case_interface import IInventoryUseCase
from .counting_dispatcher import CountingDispatcher
from apps.masterdata.models import Account, Warehouse
import logging

logger = logging.getLogger(__name__)

class InventoryUseCase(IInventoryUseCase):
    """
    Use case pour la gestion d'inventaire (création et mise à jour) avec validation métier.
    
    Ce use case permet de créer ou mettre à jour un inventaire en 3 étapes distinctes :
    1. Validation des données
    2. Création/mise à jour de l'inventaire et des settings
    3. Création/mise à jour des comptages liés à l'inventaire
    
    Exemples d'utilisation :
    
    # Création d'inventaire
    use_case = InventoryUseCase()
    result = use_case.create_inventory(data)
    
    # Mise à jour d'inventaire
    result = use_case.update_inventory(inventory_id, data)
    
    # Validation uniquement
    validation_result = use_case.validate_only(data)
    
    # Exécution étape par étape
    use_case.step1_validate_data(data)
    inventory = use_case.step2_process_inventory_and_settings(data, inventory_id)
    countings = use_case.step3_process_countings_for_inventory(inventory, data['comptages'])
    """
    
    def __init__(self, inventory_repository: InventoryRepository = None, counting_dispatcher: CountingDispatcher = None):
        self.inventory_repository = inventory_repository or InventoryRepository()
        self.counting_dispatcher = counting_dispatcher or CountingDispatcher()
    
    def create_inventory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouvel inventaire.
        
        Args:
            data: Données de l'inventaire au format JSON
            
        Returns:
            Dict[str, Any]: Résultat de la création
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        return self._process_inventory(data, inventory_id=None)
    
    def update_inventory(self, inventory_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un inventaire existant.
        
        Args:
            inventory_id: ID de l'inventaire à mettre à jour
            data: Données de l'inventaire au format JSON
            
        Returns:
            Dict[str, Any]: Résultat de la mise à jour
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        return self._process_inventory(data, inventory_id=inventory_id)
    
    def _process_inventory(self, data: Dict[str, Any], inventory_id: int = None) -> Dict[str, Any]:
        """
        Méthode générique pour traiter un inventaire (création ou mise à jour).
        
        Args:
            data: Données de l'inventaire au format JSON
            inventory_id: ID de l'inventaire à mettre à jour (None pour création)
            
        Returns:
            Dict[str, Any]: Résultat de l'opération
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        try:
            with transaction.atomic():
                # ÉTAPE 1: Validation des données
                self.step1_validate_data(data)
                
                # ÉTAPE 2: Création ou mise à jour de l'inventaire et des settings
                inventory = self.step2_process_inventory_and_settings(data, inventory_id)
                
                # ÉTAPE 3: Création ou mise à jour des comptages liés à l'inventaire
                countings = self.step3_process_countings_for_inventory(inventory, data['comptages'])
                
                # Retour du résultat formaté
                return self._format_response(inventory, countings)
                
        except Exception as e:
            operation = "mise à jour" if inventory_id else "création"
            logger.error(f"Erreur dans InventoryUseCase._process_inventory ({operation}): {str(e)}", exc_info=True)
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
        self._validate_countings(data['comptages'])
    
    def step2_process_inventory_and_settings(self, data: Dict[str, Any], inventory_id: int) -> Inventory:
        """
        Étape 2: Création ou mise à jour de l'inventaire et des settings.
        
        Args:
            data: Données de l'inventaire au format JSON
            inventory_id: ID de l'inventaire à mettre à jour (None pour création)
            
        Returns:
            Inventory: L'inventaire créé ou mis à jour
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        return self._process_inventory_and_settings(data, inventory_id)
    
    def step3_process_countings_for_inventory(self, inventory: Inventory, comptages: List[Dict[str, Any]]) -> List[Counting]:
        """
        Étape 3: Création ou mise à jour des comptages liés à l'inventaire.
        
        Args:
            inventory: L'inventaire créé ou mis à jour
            comptages: Liste des données des comptages
            
        Returns:
            List[Counting]: Liste des comptages créés ou mis à jour
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        return self._process_countings_for_inventory(inventory, comptages)
    
    def _process_inventory_and_settings(self, data: Dict[str, Any], inventory_id: int = None) -> Inventory:
        """
        Étape 2: Crée ou met à jour l'inventaire et les settings associés.
        
        Args:
            data: Données de l'inventaire
            inventory_id: ID de l'inventaire à mettre à jour (None pour création)
            
        Returns:
            Inventory: L'inventaire créé ou mis à jour
        """
        # Création ou mise à jour de l'inventaire
        if inventory_id:
            try:
                inventory = Inventory.objects.get(id=inventory_id, is_deleted=False)
                inventory.label = data['label']
                inventory.date = data['date']
                inventory.save()
                
                # Suppression des anciens settings
                inventory.awi_links.all().delete()
            except Inventory.DoesNotExist:
                raise InventoryValidationError(f"Inventaire avec l'ID {inventory_id} non trouvé")
        else:
            # Création de l'inventaire
            inventory_data = {
                'label': data['label'],
                'date': data['date'],
                'status': 'EN PREPARATION'
            }
            inventory = Inventory.objects.create(**inventory_data)
        
        # Création des settings (liens entre inventaire, entrepôts et compte)
        account_id = data['account_id']
        for warehouse_info in data['warehouse']:
            warehouse_id = warehouse_info['id']
            Setting.objects.create(
                inventory=inventory,
                warehouse_id=warehouse_id,
                account_id=account_id
            )
        
        operation = "mis à jour" if inventory_id else "créé"
        logger.info(f"Inventaire {inventory.id} {operation} avec {len(data['warehouse'])} entrepôts")
        return inventory
    
    def _process_countings_for_inventory(self, inventory: Inventory, comptages: List[Dict[str, Any]]) -> List[Counting]:
        """
        Étape 3: Crée ou met à jour les comptages liés à l'inventaire.
        
        Args:
            inventory: L'inventaire créé ou mis à jour
            comptages: Liste des données des comptages
            
        Returns:
            List[Counting]: Liste des comptages créés ou mis à jour
        """
        # Suppression des anciens comptages si mise à jour
        if inventory.countings.exists():
            inventory.countings.all().delete()
        
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
        
        # Validation des champs obligatoires
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
        
        if not data.get('comptages'):
            errors.append("Au moins un comptage est obligatoire")
        elif not isinstance(data['comptages'], list) or len(data['comptages']) == 0:
            errors.append("La liste des comptages ne peut pas être vide")
        
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
        for warehouse_info in data['warehouse']:
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
        
        Règles métier :
        1. "image stock" ne peut être que dans le 1er comptage (order=1)
        2. Si le 1er comptage est "image stock", les 2e et 3e doivent être du même mode (soit "en vrac", soit "par article")
        3. Si le 1er comptage n'est pas "image stock", tous les comptages peuvent être "par article" ou "en vrac"
        4. Validation de cohérence entre les comptages
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
        valid_modes = ['en vrac', 'par article', 'image stock']
        for i, mode in enumerate(count_modes):
            if mode not in valid_modes:
                errors.append(f"Comptage {i+1}: Mode de comptage invalide '{mode}'")
        
        # Validation des combinaisons autorisées
        first_mode = count_modes[0]
        second_mode = count_modes[1]
        third_mode = count_modes[2]
        
        # Scénario 1: Premier comptage = "image stock"
        if first_mode == "image stock":
            # Les 2e et 3e comptages doivent être du même mode (soit "en vrac", soit "par article")
            if second_mode != third_mode:
                errors.append("Si le premier comptage est 'image stock', les 2e et 3e comptages doivent avoir le même mode")
            
            if second_mode not in ["en vrac", "par article"]:
                errors.append("Si le premier comptage est 'image stock', les 2e et 3e comptages doivent être 'en vrac' ou 'par article'")
        
        # Scénario 2: Premier comptage = "en vrac" ou "par article"
        elif first_mode in ["en vrac", "par article"]:
            # Tous les comptages doivent être "en vrac" ou "par article"
            for i, mode in enumerate(count_modes):
                if mode not in ["en vrac", "par article"]:
                    errors.append(f"Si le premier comptage n'est pas 'image stock', tous les comptages doivent être 'en vrac' ou 'par article' (comptage {i+1}: '{mode}')")
        
        # Validation de cohérence entre les comptages
        self._validate_counting_consistency(comptages_sorted, errors)
        
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
    
    def _validate_counting_consistency(self, comptages_sorted: List[Dict[str, Any]], errors: List[str]) -> None:
        """
        Valide la cohérence entre les comptages.
        
        Règles de cohérence :
        1. Si 1er comptage = "image stock", les 2e et 3e doivent avoir la même configuration
        2. Si 1er comptage n'est pas "image stock", le 3e comptage doit avoir soit la config du 1er OU la config du 2e
        """
        first_comptage = comptages_sorted[0]
        second_comptage = comptages_sorted[1]
        third_comptage = comptages_sorted[2]
        
        first_mode = first_comptage.get('count_mode')
        
        # Règle 1: Si 1er comptage = "image stock", le 3e doit avoir la même configuration que le 2e
        if first_mode == "image stock":
            # Vérifier que le 3e comptage a la même configuration que le 2e
            second_config = self._get_counting_config(second_comptage)
            third_config = self._get_counting_config(third_comptage)
            
            if third_config != second_config:
                errors.append("Si le premier comptage est 'image stock', le 3e comptage doit avoir la même configuration que le 2e comptage")
        
        # Règle 2: Si 1er comptage n'est pas "image stock", le 3e comptage doit avoir soit la config du 1er OU la config du 2e
        else:
            # Le 3e comptage doit avoir soit la config du 1er OU la config du 2e
            first_config = self._get_counting_config(first_comptage)
            second_config = self._get_counting_config(second_comptage)
            third_config = self._get_counting_config(third_comptage)
            
            # Vérifier si le 3e a la même config que le 1er OU le 2e
            matches_first = third_config == first_config
            matches_second = third_config == second_config
            
            if not (matches_first or matches_second):
                errors.append("Si le premier comptage n'est pas 'image stock', le 3e comptage doit avoir soit la même configuration que le 1er OU la même configuration que le 2e")
    
    def _get_counting_config(self, comptage: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrait la configuration d'un comptage pour comparaison.
        
        Args:
            comptage: Données du comptage
            
        Returns:
            Dict[str, Any]: Configuration du comptage
        """
        return {
            'count_mode': comptage.get('count_mode'),
            'unit_scanned': comptage.get('unit_scanned', False),
            'entry_quantity': comptage.get('entry_quantity', False),
            'is_variant': comptage.get('is_variant', False),
            'n_lot': comptage.get('n_lot', False),
            'n_serie': comptage.get('n_serie', False),
            'dlc': comptage.get('dlc', False),
            'show_product': comptage.get('show_product', False),
            'stock_situation': comptage.get('stock_situation', False),
            'quantity_show': comptage.get('quantity_show', False)
        }
    
    def _format_response(self, inventory: Inventory, countings: List[Counting]) -> Dict[str, Any]:
        """
        Formate la réponse de création ou de mise à jour.
        """
        return {
            "success": True,
            "inventory": {
                "id": inventory.id,
                "label": inventory.label,
                "date": inventory.date,
                "status": inventory.status
            },
            "countings": [
                {
                    "id": counting.id,
                    "order": counting.order,
                    "count_mode": counting.count_mode,
                }
                for counting in countings
            ]
        }
    
    def validate_only(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide uniquement les données sans créer l'inventaire.
        
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
            self._validate_countings(data['comptages'])
            
            return {
                "success": True,
                "message": "Données validées avec succès"
            }
            
        except Exception as e:
            logger.error(f"Erreur de validation dans InventoryUseCase: {str(e)}", exc_info=True)
            raise 