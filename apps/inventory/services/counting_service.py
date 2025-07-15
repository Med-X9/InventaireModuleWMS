"""
Service pour la gestion des comptages d'inventaire.
"""
from typing import Dict, Any, List
from django.utils import timezone
from ..interfaces.counting_interface import ICountingService
from ..repositories import InventoryRepository
from ..exceptions import CountingValidationError
from ..models import Counting, Inventory
from ..usecases import CountingByArticle, CountingByInBulk, CountingByStockimage

class CountingService(ICountingService):
    """Service pour la gestion des comptages d'inventaire."""   
    
    def __init__(self, repository: InventoryRepository = None):
        self.repository = repository or InventoryRepository()

    def create_counting(self, data: Dict[str, Any]) -> Counting:
        """
        Crée un nouveau comptage.
        
        Args:
            data: Les données du comptage
            
        Returns:
            Counting: Le comptage créé
            
        Raises:
            CountingValidationError: Si les données sont invalides
        """
        # Créer l'objet Counting sans sauvegarder
        counting = Counting(
            inventory_id=data['inventory_id'],
            order=data['order'],
            count_mode=data['count_mode'],
            unit_scanned=data.get('unit_scanned', False),
            entry_quantity=data.get('entry_quantity', False),
            stock_situation=data.get('stock_situation', False),
            is_variant=data.get('is_variant', False),
            n_lot=data.get('n_lot', False),
            n_serie=data.get('n_serie', False),
            dlc=data.get('dlc', False),
            show_product=data.get('show_product', False),
            quantity_show=data.get('quantity_show', False),
        )
        
        # Générer la référence manuellement
        counting.reference = counting.generate_reference(counting.REFERENCE_PREFIX)
        
        # Sauvegarder l'objet
        counting.save()
        
        return counting

    def create_countings(self, inventory_id: int, comptages_data: List[Dict[str, Any]]) -> List[Counting]:
        """
        Crée plusieurs comptages pour un inventaire en utilisant les use cases appropriés.
        
        Args:
            inventory_id: L'ID de l'inventaire
            comptages_data: Liste des données des comptages
            
        Returns:
            List[Counting]: Liste des comptages créés
            
        Raises:
            CountingValidationError: Si les données sont invalides
        """
        countings = []
        
        for comptage_data in comptages_data:
            comptage_data['inventory_id'] = inventory_id
            
            # Sélection du use case approprié selon le mode de comptage
            count_mode = comptage_data.get('count_mode')
            
            if count_mode == "en vrac":
                use_case = CountingByInBulk()
            elif count_mode == "par article":
                use_case = CountingByArticle()
            elif count_mode == "image de stock":
                use_case = CountingByStockimage()
            else:
                raise CountingValidationError(f"Mode de comptage non supporté: {count_mode}")
            
            # Création du comptage via le use case approprié
            counting = use_case.create_counting(comptage_data)
            countings.append(counting)
        
        return countings
    
    def validate_countings_consistency(self, comptages: List[Dict[str, Any]]) -> None:
        """
        Valide la cohérence des modes de comptage selon les règles métier.
        
        Règles métier :
        1. "image stock" ne peut être que dans le 1er comptage (order=1)
        2. Si le 1er comptage est "image stock", les 2e et 3e doivent être du même mode (soit "en vrac", soit "par article")
        3. Si le 1er comptage n'est pas "image stock", tous les comptages peuvent être "par article" ou "en vrac"
        
        Args:
            comptages: Liste des données des comptages
            
        Raises:
            CountingValidationError: Si les règles métier ne sont pas respectées
        """
        errors = []
        
        # Vérifier qu'il y a exactement 3 comptages
        if len(comptages) != 3:
            raise CountingValidationError("Un inventaire doit contenir exactement 3 comptages")
        
        # Trier les comptages par ordre
        comptages_sorted = sorted(comptages, key=lambda x: x.get('order', 0))
        
        # Vérifier que les ordres sont 1, 2, 3
        orders = [c.get('order') for c in comptages_sorted]
        if orders != [1, 2, 3]:
            raise CountingValidationError("Les comptages doivent avoir les ordres 1, 2, 3")
        
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
        
        if errors:
            raise CountingValidationError(" | ".join(errors))

    def validate_counting_data(self, comptage_data: Dict[str, Any]) -> None:
        """
        Valide les données d'un comptage individuel.
        
        Args:
            comptage_data: Les données du comptage
            
        Raises:
            CountingValidationError: Si les données sont invalides
        """
        errors = []
        
        # Validation des champs obligatoires
        if not comptage_data.get('order'):
            errors.append("L'ordre du comptage est obligatoire")
        
        if not comptage_data.get('count_mode'):
            errors.append("Le mode de comptage est obligatoire")
        
        # Validation du mode de comptage
        count_mode = comptage_data.get('count_mode')
        if count_mode and count_mode not in ['en vrac', 'par article', 'image stock']:
            errors.append(f"Mode de comptage invalide: {count_mode}")
        
        if errors:
            raise CountingValidationError(" | ".join(errors)) 