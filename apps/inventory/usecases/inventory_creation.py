"""
Use case pour la création d'inventaire.
"""
from typing import Dict, Any, List
from django.utils import timezone
from django.db import transaction
from ..models import Inventory, Setting, Counting
from ..exceptions import InventoryValidationError
from ..repositories.inventory_repository import InventoryRepository
from .counting_dispatcher import CountingDispatcher
from apps.masterdata.models import Account, Warehouse
import logging

logger = logging.getLogger(__name__)

class InventoryCreationUseCase:
    """
    Use case pour la création d'inventaire avec validation métier.
    
    Ce use case permet de créer un inventaire en 3 étapes distinctes :
    1. Validation des données
    2. Création de l'inventaire et des settings
    3. Création des comptages liés à l'inventaire
    
    Exemples d'utilisation :
    
    # Création complète en une fois
    use_case = InventoryCreationUseCase()
    result = use_case.execute(data)
    
    # Validation uniquement
    validation_result = use_case.validate_only(data)
    
    # Exécution étape par étape
    use_case.step1_validate_data(data)
    inventory = use_case.step2_create_inventory_and_settings(data)
    countings = use_case.step3_create_countings(inventory, data['comptages'])
    """
    
    def __init__(self, inventory_repository: InventoryRepository = None, counting_dispatcher: CountingDispatcher = None):
        self.inventory_repository = inventory_repository or InventoryRepository()
        self.counting_dispatcher = counting_dispatcher or CountingDispatcher()
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
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
                inventory = self.step2_create_inventory_and_settings(data)
                
                # ÉTAPE 3: Création des comptages liés à l'inventaire créé
                countings = self.step3_create_countings(inventory, data['comptages'])
                
                # Retour du résultat formaté
                return self._format_response(inventory, countings)
                
        except Exception as e:
            logger.error(f"Erreur dans InventoryCreationUseCase: {str(e)}", exc_info=True)
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
    
    def step2_create_inventory_and_settings(self, data: Dict[str, Any]) -> Inventory:
        """
        Étape 2: Création de l'inventaire et des settings.
        
        Args:
            data: Données de l'inventaire au format JSON
            
        Returns:
            Inventory: L'inventaire créé
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        return self._create_inventory_and_settings(data)
    
    def step3_create_countings(self, inventory: Inventory, comptages: List[Dict[str, Any]]) -> List[Counting]:
        """
        Étape 3: Création des comptages liés à l'inventaire.
        
        Args:
            inventory: L'inventaire créé
            comptages: Liste des données des comptages
            
        Returns:
            List[Counting]: Liste des comptages créés
            
        Raises:
            InventoryValidationError: Si les données sont invalides
        """
        return self._create_countings_for_inventory(inventory, comptages)
    
    def _create_inventory_and_settings(self, data: Dict[str, Any]) -> Inventory:
        """
        Étape 2: Crée l'inventaire et les settings associés.
        
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
    
    def _create_countings_for_inventory(self, inventory: Inventory, comptages: List[Dict[str, Any]]) -> List[Counting]:
        """
        Étape 3: Crée les comptages liés à l'inventaire créé.
        
        Args:
            inventory: L'inventaire créé
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
        1. Le 1er comptage doit être défini (order=1) et pilote les modes suivants.
        2. Si le 1er comptage est "image de stock", les 2e et 3e doivent partager le même mode.
        3. Si le 1er comptage est "par article", tous les comptages doivent rester "par article" avec les mêmes paramètres (N° lot, DLC, N° série).
        4. Si le 1er comptage est "en vrac", les 2e et 3e doivent rester "en vrac".
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
        normalized_modes = [self._normalize_count_mode(mode) for mode in count_modes]
        
        # Vérifier que tous les modes sont valides
        valid_modes = ['en vrac', 'par article', 'image de stock']
        for i, mode in enumerate(normalized_modes):
            if mode not in valid_modes:
                errors.append(f"Comptage {i+1}: Mode de comptage invalide '{count_modes[i]}'")
        
        # Validation des combinaisons autorisées
        first_mode = normalized_modes[0]
        second_mode = normalized_modes[1]
        third_mode = normalized_modes[2]
        article_param_fields = ['n_lot', 'dlc', 'n_serie', 'is_variant']
        article_field_labels = {
            'n_lot': "N° lot",
            'dlc': "DLC",
            'n_serie': "N° série",
            'is_variant': "Variante",
        }
        article_fields_label_joined = ", ".join(article_field_labels[field] for field in article_param_fields)
        
        # Scénario 1: Premier comptage = "image de stock"
        if first_mode == "image de stock":
            if second_mode != third_mode:
                errors.append("Si le premier comptage est 'image de stock', les 2e et 3e comptages doivent avoir le même mode")
            
            if second_mode not in ["en vrac", "par article"]:
                errors.append("Si le premier comptage est 'image de stock', les 2e et 3e comptages doivent être 'en vrac' ou 'par article'")
            
            if second_mode == "par article":
                second_params = self._extract_article_params(comptages_sorted[1], article_param_fields)
                third_params = self._extract_article_params(comptages_sorted[2], article_param_fields)
                if second_params != third_params:
                    errors.append(
                        f"Les comptages 2 et 3 en mode 'par article' doivent partager les mêmes paramètres ({article_fields_label_joined})"
                    )
        
        # Scénario 2: Premier comptage = "par article"
        elif first_mode == "par article":
            if second_mode != "par article" or third_mode != "par article":
                errors.append("Si le premier comptage est 'par article', les 2e et 3e comptages doivent également être 'par article'")
            else:
                first_params = self._extract_article_params(comptages_sorted[0], article_param_fields)
                for index, counting in enumerate(comptages_sorted[1:], start=2):
                    counting_params = self._extract_article_params(counting, article_param_fields)
                    if counting_params != first_params:
                        order_value = counting.get('order', index)
                        differing_fields = [
                            article_field_labels[field] for field in article_param_fields if counting_params[field] != first_params[field]
                        ]
                        formatted_fields = ", ".join(differing_fields)
                        errors.append(
                            f"Comptage {order_value}: Les paramètres ({formatted_fields}) doivent être identiques au premier comptage 'par article'"
                        )
        
        # Scénario 3: Premier comptage = "en vrac"
        elif first_mode == "en vrac":
            if second_mode != "en vrac" or third_mode != "en vrac":
                errors.append("Si le premier comptage est 'en vrac', les 2e et 3e comptages doivent également être 'en vrac'")
        
        # Validation de cohérence entre les comptages
        self._validate_counting_consistency(comptages_sorted, errors)
        
        # Validation des champs obligatoires et spécifiques via CountingDispatcher
        for i, comptage in enumerate(comptages_sorted, 1):
            if not comptage.get('order'):
                errors.append(f"Comptage {i}: L'ordre est obligatoire")
            
            if not comptage.get('count_mode'):
                errors.append(f"Comptage {i}: Le mode de comptage est obligatoire")
            
            count_mode = comptage.get('count_mode')
            if count_mode:
                try:
                    self.counting_dispatcher.validate_counting_data(comptage)
                except Exception as e:
                    errors.append(f"Comptage {i}: {str(e)}")
        
        if errors:
            raise InventoryValidationError(" | ".join(errors))
    
    def _validate_counting_consistency(self, comptages_sorted: List[Dict[str, Any]], errors: List[str]) -> None:
        """
        Valide la cohérence entre les comptages.
        
        Règles de cohérence :
        1. Si 1er comptage = "image de stock", les 2e et 3e doivent partager la même configuration.
        2. Si 1er comptage = "par article", les trois comptages doivent partager la même configuration.
        3. Si 1er comptage = "en vrac", les trois comptages restent en "en vrac".
        """
        first_comptage = comptages_sorted[0]
        second_comptage = comptages_sorted[1]
        third_comptage = comptages_sorted[2]
        
        first_mode = self._normalize_count_mode(first_comptage.get('count_mode'))
        second_mode = self._normalize_count_mode(second_comptage.get('count_mode'))
        third_mode = self._normalize_count_mode(third_comptage.get('count_mode'))
        
        if first_mode == "image de stock":
            second_config = self._get_counting_config(second_comptage)
            third_config = self._get_counting_config(third_comptage)
            if third_config != second_config:
                errors.append("Si le premier comptage est 'image de stock', le 3e comptage doit avoir la même configuration que le 2e comptage")
        
        elif first_mode == "par article":
            first_config = self._get_counting_config(first_comptage)
            second_config = self._get_counting_config(second_comptage)
            third_config = self._get_counting_config(third_comptage)
            if second_config != first_config:
                errors.append("Si le premier comptage est 'par article', le 2e comptage doit avoir la même configuration que le 1er comptage")
            if third_config != first_config:
                errors.append("Si le premier comptage est 'par article', le 3e comptage doit avoir la même configuration que le 1er comptage")
        
        elif first_mode == "en vrac":
            if second_mode != "en vrac" or third_mode != "en vrac":
                errors.append("Si le premier comptage est 'en vrac', tous les comptages doivent rester en 'en vrac'")
    
    def _get_counting_config(self, comptage: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrait la configuration d'un comptage pour comparaison.
        
        Args:
            comptage: Données du comptage
            
        Returns:
            Dict[str, Any]: Configuration du comptage
        """
        return {
            'count_mode': self._normalize_count_mode(comptage.get('count_mode')),
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

    def _extract_article_params(self, comptage: Dict[str, Any], fields: List[str]) -> Dict[str, bool]:
        """
        Extrait et normalise les paramètres spécifiques au mode 'par article'.
        """
        return {field: bool(comptage.get(field, False)) for field in fields}

    def _normalize_count_mode(self, mode: Any) -> str:
        """
        Normalise le mode de comptage pour simplifier les comparaisons.
        """
        if not isinstance(mode, str):
            return ""
        normalized = mode.strip().lower()
        if normalized in ["image stock", "image de stock"]:
            return "image de stock"
        return normalized
    
    def _format_response(self, inventory: Inventory, countings: List[Counting]) -> Dict[str, Any]:
        """
        Formate la réponse de création.
        """
        return {
            "success": True,
            "message": "Inventaire créé avec succès"
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
            logger.error(f"Erreur de validation dans InventoryCreationUseCase: {str(e)}", exc_info=True)
            raise 