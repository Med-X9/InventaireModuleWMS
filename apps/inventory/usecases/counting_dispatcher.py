"""
Use case pour le dispatcher de comptages.
"""
from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import models, transaction
from ..models import Counting, CountingDetail, Job, JobDetail, Assigment, Personne, Inventory
from ..exceptions import CountingValidationError
from .counting_by_article import CountingByArticle
from .counting_by_in_bulk import CountingByInBulk
from .counting_by_stockimage import CountingByStockimage


class CountingDispatcher:
    """
    Use case pour dispatcher les comptages d'inventaire vers les bons use cases.
    
    Ce use case permet de :
    - Sélectionner le use case approprié selon le mode de comptage
    - Diriger les comptages vers les bons use cases
    """
    
    def __init__(self):
        self.counting_service = None  # Sera injecté via DI
    
    def get_use_case_for_counting(self, counting: Counting):
        """
        Retourne le use case approprié selon le mode de comptage.
        
        Args:
            counting: Le comptage
            
        Returns:
            Le use case approprié
            
        Raises:
            CountingValidationError: Si le mode de comptage n'est pas supporté
        """
        count_mode = counting.count_mode
        
        if count_mode == "en vrac":
            return CountingByInBulk()
        elif count_mode == "par article":
            return CountingByArticle()
        elif count_mode == "image stock":
            return CountingByStockimage()
        else:
            raise CountingValidationError(f"Mode de comptage non supporté: {count_mode}")
    
    def get_use_cases_for_inventory(self, inventory_id: int) -> Dict[str, Any]:
        """
        Récupère tous les use cases nécessaires pour un inventaire.
        
        Args:
            inventory_id: L'ID de l'inventaire
            
        Returns:
            Dict[str, Any]: Dictionnaire avec les comptages et leurs use cases associés
            
        Raises:
            CountingValidationError: Si l'inventaire n'existe pas ou s'il n'y a pas de comptages
        """
        # Récupération de l'inventaire
        try:
            inventory = Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            raise CountingValidationError(f"Inventaire avec l'ID {inventory_id} non trouvé")
        
        # Récupération des comptages de l'inventaire
        countings = Counting.objects.filter(inventory=inventory)
        
        if not countings.exists():
            raise CountingValidationError("Aucun comptage trouvé pour cet inventaire")
        
        # Association des comptages avec leurs use cases
        counting_use_cases = {}
        
        for counting in countings:
            use_case = self.get_use_case_for_counting(counting)
            counting_use_cases[counting.id] = {
                'counting': counting,
                'use_case': use_case,
                'count_mode': counting.count_mode
            }
        
        return {
            'inventory': inventory,
            'counting_use_cases': counting_use_cases,
            'total_countings': len(counting_use_cases)
        }
    
    def validate_counting_mode(self, count_mode: str) -> bool:
        """
        Valide si un mode de comptage est supporté.
        
        Args:
            count_mode: Le mode de comptage à valider
            
        Returns:
            bool: True si le mode est supporté, False sinon
        """
        supported_modes = ["en vrac", "par article", "image stock"]
        return count_mode in supported_modes
    
    def get_supported_counting_modes(self) -> List[str]:
        """
        Retourne la liste des modes de comptage supportés.
        
        Returns:
            List[str]: Liste des modes de comptage supportés
        """
        return ["en vrac", "par article", "image stock"]
    
    def validate_counting_data(self, counting_data: Dict[str, Any]) -> None:
        """
        Valide les données d'un comptage via le use case approprié.
        
        Args:
            counting_data: Les données du comptage à valider
            
        Raises:
            CountingValidationError: Si les données sont invalides
        """
        count_mode = counting_data.get('count_mode')
        
        if count_mode == "en vrac":
            use_case = CountingByInBulk()
        elif count_mode == "par article":
            use_case = CountingByArticle()
        elif count_mode == "image stock":
            use_case = CountingByStockimage()
        else:
            raise CountingValidationError(f"Mode de comptage non supporté: {count_mode}")
        
        # Valider via le use case approprié
        use_case.validate_counting_data(counting_data) 