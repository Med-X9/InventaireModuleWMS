"""
Use case pour la validation en lot de CountingDetail.

Ce use case respecte les principes SOLID, KISS et DRY :
- Single Responsibility : Valide uniquement les données
- Open/Closed : Extensible sans modification
- Dependency Inversion : Dépend des abstractions (modèles Django)
- KISS : Logique simple et claire
- DRY : Réutilise la validation existante
"""

from typing import Dict, Any, List, Optional
from django.core.exceptions import ValidationError

from apps.inventory.models import Counting, JobDetail, Assigment
from apps.masterdata.models import Product, Location
import logging

logger = logging.getLogger(__name__)


class CountingDetailBatchValidationUseCase:
    """
    Use case pour valider en lot des données de CountingDetail.
    
    Responsabilité unique : Valider les données avant création/mise à jour.
    
    Exemple d'utilisation :
        use_case = CountingDetailBatchValidationUseCase()
        results = use_case.execute(data_list, related_cache)
        
        for i, result in enumerate(results):
            if not result['valid']:
                print(f"Erreur élément {i}: {result['error']}")
    """
    
    def __init__(self):
        """Initialise le use case."""
        pass
    
    def execute(
        self, 
        data_list: List[Dict[str, Any]], 
        related_cache: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Valide tous les éléments en lot en utilisant un cache préchargé.
        
        Args:
            data_list: Liste des données à valider
            related_cache: Cache des objets liés préchargés avec les clés :
                - 'countings': Dict[counting_id, Counting]
                - 'locations': Dict[location_id, Location]
                - 'products': Dict[product_id, Product]
                - 'assignments': Dict[assignment_id, Assigment]
                - 'job_details': Dict[(job_id, counting_id, location_id), JobDetail]
        
        Returns:
            List[Dict] avec pour chaque élément :
                - 'valid': bool - True si valide
                - 'error': str ou None - Message d'erreur si invalide
                - 'related_objects': Dict - Objets liés validés (counting, location, etc.)
        
        Raises:
            ValidationError: Si tous les éléments sont invalides (optionnel)
        """
        results = []
        
        for data in data_list:
            result = self._validate_single_item(data, related_cache)
            results.append(result)
        
        return results
    
    def _validate_single_item(
        self, 
        data: Dict[str, Any], 
        related_cache: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Valide un seul élément de données.
        
        Args:
            data: Données à valider
            related_cache: Cache des objets liés
        
        Returns:
            Dict avec 'valid', 'error', 'related_objects'
        """
        result = {'valid': True, 'error': None, 'related_objects': {}}
        
        try:
            # Validation Counting
            counting = self._validate_counting(data, related_cache)
            if not counting:
                return {'valid': False, 'error': "Le champ 'counting_id' est obligatoire", 'related_objects': {}}
            result['related_objects']['counting'] = counting
            
            # Validation Location
            location = self._validate_location(data, related_cache)
            if not location:
                return {'valid': False, 'error': "Le champ 'location_id' est obligatoire", 'related_objects': {}}
            result['related_objects']['location'] = location
            
            # Validation Product (optionnel selon mode)
            product = self._validate_product(data, counting, related_cache)
            if product is False:  # False signifie erreur, None signifie optionnel
                return {'valid': False, 'error': "Produit invalide ou manquant", 'related_objects': {}}
            result['related_objects']['product'] = product
            
            # Validation Assignment
            assignment = self._validate_assignment(data, related_cache)
            if not assignment:
                return {'valid': False, 'error': "Le champ 'assignment_id' est obligatoire", 'related_objects': {}}
            result['related_objects']['assignment'] = assignment
            
            # Validation JobDetail
            job_detail = self._validate_job_detail(assignment, counting, location, related_cache)
            if not job_detail:
                return {
                    'valid': False, 
                    'error': f"JobDetail non trouvé pour job {assignment.job_id}, counting {counting.id}, location {location.id}",
                    'related_objects': {}
                }
            result['related_objects']['job_detail'] = job_detail
            
            # Validation quantité
            quantity_error = self._validate_quantity(data)
            if quantity_error:
                return {'valid': False, 'error': quantity_error, 'related_objects': {}}
            
            # Validation propriétés produit
            product_props_error = self._validate_product_properties(data, counting, product)
            if product_props_error:
                return {'valid': False, 'error': product_props_error, 'related_objects': {}}
            
            # Tout est valide
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation: {str(e)}")
            return {'valid': False, 'error': f"Erreur de validation: {str(e)}", 'related_objects': {}}
    
    def _validate_counting(
        self, 
        data: Dict[str, Any], 
        related_cache: Dict[str, Any]
    ) -> Optional[Counting]:
        """
        Valide et récupère le Counting.
        
        Args:
            data: Données à valider
            related_cache: Cache des objets liés
        
        Returns:
            Counting ou None si invalide
        """
        counting_id = data.get('counting_id')
        if not counting_id:
            return None
        
        counting = related_cache['countings'].get(counting_id)
        if not counting:
            return None
        
        return counting
    
    def _validate_location(
        self, 
        data: Dict[str, Any], 
        related_cache: Dict[str, Any]
    ) -> Optional[Location]:
        """
        Valide et récupère la Location.
        
        Args:
            data: Données à valider
            related_cache: Cache des objets liés
        
        Returns:
            Location ou None si invalide
        """
        location_id = data.get('location_id')
        if not location_id:
            return None
        
        location = related_cache['locations'].get(location_id)
        if not location:
            return None
        
        return location
    
    def _validate_product(
        self, 
        data: Dict[str, Any], 
        counting: Counting, 
        related_cache: Dict[str, Any]
    ) -> Optional[Product]:
        """
        Valide et récupère le Product.
        
        Args:
            data: Données à valider
            counting: Le Counting (pour vérifier le mode)
            related_cache: Cache des objets liés
        
        Returns:
            Product si valide, None si optionnel, False si erreur
        """
        product_id = data.get('product_id')
        
        # Mode "par article" nécessite un produit
        if counting.count_mode == "par article" and not product_id:
            return False
        
        # Si pas de product_id, c'est optionnel (mode "en vrac" ou "image de stock")
        if not product_id:
            return None
        
        product = related_cache['products'].get(product_id)
        if not product:
            return False
        
        return product
    
    def _validate_assignment(
        self, 
        data: Dict[str, Any], 
        related_cache: Dict[str, Any]
    ) -> Optional[Assigment]:
        """
        Valide et récupère l'Assigment.
        
        Args:
            data: Données à valider
            related_cache: Cache des objets liés
        
        Returns:
            Assigment ou None si invalide
        """
        assignment_id = data.get('assignment_id')
        if not assignment_id:
            return None
        
        assignment = related_cache['assignments'].get(assignment_id)
        if not assignment:
            return None
        
        return assignment
    
    def _validate_job_detail(
        self, 
        assignment: Assigment, 
        counting: Counting, 
        location: Location, 
        related_cache: Dict[str, Any]
    ) -> Optional[JobDetail]:
        """
        Valide et récupère le JobDetail.
        
        Args:
            assignment: L'Assigment
            counting: Le Counting
            location: La Location
            related_cache: Cache des objets liés
        
        Returns:
            JobDetail ou None si non trouvé
        """
        job_detail_key = (assignment.job_id, counting.id, location.id)
        job_detail = related_cache['job_details'].get(job_detail_key)
        return job_detail
    
    def _validate_quantity(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Valide la quantité inventoriée.
        
        Args:
            data: Données à valider
        
        Returns:
            Message d'erreur ou None si valide
        """
        quantity = data.get('quantity_inventoried')
        if quantity is None:
            return "La quantité inventoriée est obligatoire"
        
        try:
            quantity = int(quantity)
            if quantity < 0:
                return "La quantité inventoriée ne peut pas être négative"
        except (ValueError, TypeError):
            return "La quantité inventoriée doit être un nombre entier"
        
        return None
    
    def _validate_product_properties(
        self, 
        data: Dict[str, Any], 
        counting: Counting, 
        product: Optional[Product]
    ) -> Optional[str]:
        """
        Valide les propriétés du produit selon le mode de comptage.
        
        Args:
            data: Données à valider
            counting: Le Counting
            product: Le Product (peut être None)
        
        Returns:
            Message d'erreur ou None si valide
        """
        if not product or counting.count_mode != "par article":
            return None
        
        # Validation DLC
        if counting.dlc and product.dlc and not data.get('dlc'):
            return "Le champ 'dlc' est obligatoire"
        
        # Validation n_lot
        if counting.n_lot and product.n_lot and not data.get('n_lot'):
            return "Le champ 'n_lot' est obligatoire"
        
        return None

