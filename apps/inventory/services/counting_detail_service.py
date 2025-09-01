"""
Service pour la gestion des CountingDetail et NumeroSerie.
"""
from typing import Dict, Any, List, Optional
from django.utils import timezone
from ..usecases.counting_detail_creation import CountingDetailCreationUseCase
from ..exceptions import CountingValidationError
from ..models import CountingDetail, NSerieInventory, Counting
import logging

logger = logging.getLogger(__name__)

class CountingDetailService:
    """
    Service pour la gestion des CountingDetail et NumeroSerie.
    
    Ce service utilise le use case CountingDetailCreationUseCase pour :
    - Créer des CountingDetail
    - Créer des NumeroSerie associés
    - Mettre à jour les statuts des JobDetail
    """
    
    def __init__(self):
        self.use_case = CountingDetailCreationUseCase()
    
    def create_counting_detail(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un CountingDetail et ses NumeroSerie associés.
        
        Args:
            data: Données du comptage détaillé
            
        Returns:
            Dict[str, Any]: Résultat de la création
            
        Raises:
            CountingValidationError: Si les données sont invalides
        """
        try:
            logger.info(f"Création d'un CountingDetail avec les données: {data}")
            
            result = self.use_case.execute(data)
            
            logger.info(f"CountingDetail créé avec succès: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du CountingDetail: {str(e)}")
            raise
    
    def get_counting_details_by_counting(self, counting_id: int) -> List[CountingDetail]:
        """
        Récupère tous les CountingDetail d'un comptage.
        
        Args:
            counting_id: ID du comptage
            
        Returns:
            List[CountingDetail]: Liste des CountingDetail
        """
        try:
            counting = Counting.objects.get(id=counting_id)
            return CountingDetail.objects.filter(counting=counting).order_by('-created_at')
        except Counting.DoesNotExist:
            logger.warning(f"Comptage avec l'ID {counting_id} non trouvé")
            return []
    
    def get_counting_details_by_location(self, location_id: int) -> List[CountingDetail]:
        """
        Récupère tous les CountingDetail d'un emplacement.
        
        Args:
            location_id: ID de l'emplacement
            
        Returns:
            List[CountingDetail]: Liste des CountingDetail
        """
        return CountingDetail.objects.filter(location_id=location_id).order_by('-created_at')
    
    def get_counting_details_by_product(self, product_id: int) -> List[CountingDetail]:
        """
        Récupère tous les CountingDetail d'un produit.
        
        Args:
            product_id: ID du produit
            
        Returns:
            List[CountingDetail]: Liste des CountingDetail
        """
        return CountingDetail.objects.filter(product_id=product_id).order_by('-created_at')
    
    def get_numeros_serie_by_counting_detail(self, counting_detail_id: int) -> List[NSerieInventory]:
        """
        Récupère tous les NumeroSerie d'un CountingDetail.
        
        Args:
            counting_detail_id: ID du CountingDetail
            
        Returns:
            List[NSerieInventory]: Liste des NumeroSerie
        """
        try:
            counting_detail = CountingDetail.objects.get(id=counting_detail_id)
            return NSerieInventory.objects.filter(counting_detail=counting_detail)
        except CountingDetail.DoesNotExist:
            logger.warning(f"CountingDetail avec l'ID {counting_detail_id} non trouvé")
            return []
    
    def validate_counting_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide les données d'un comptage sans créer l'objet.
        
        Args:
            data: Données à valider
            
        Returns:
            Dict[str, Any]: Résultat de la validation
        """
        try:
            # Créer une copie des données pour la validation
            validation_data = data.copy()
            
            # Simuler la validation en essayant de récupérer les objets liés
            if 'counting_id' in validation_data:
                Counting.objects.get(id=validation_data['counting_id'])
            
            if 'location_id' in validation_data:
                from apps.masterdata.models import Location
                Location.objects.get(id=validation_data['location_id'])
            
            if 'product_id' in validation_data:
                from apps.masterdata.models import Product
                Product.objects.get(id=validation_data['product_id'])
            
            return {
                'valid': True,
                'message': 'Données valides'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def get_counting_summary(self, counting_id: int) -> Dict[str, Any]:
        """
        Récupère un résumé des comptages pour un comptage donné.
        
        Args:
            counting_id: ID du comptage
            
        Returns:
            Dict[str, Any]: Résumé des comptages
        """
        try:
            counting = Counting.objects.get(id=counting_id)
            counting_details = CountingDetail.objects.filter(counting=counting)
            
            total_quantity = sum(cd.quantity_inventoried for cd in counting_details)
            total_numeros_serie = sum(
                NSerieInventory.objects.filter(counting_detail=cd).count() 
                for cd in counting_details
            )
            
            return {
                'counting_id': counting_id,
                'count_mode': counting.count_mode,
                'total_counting_details': counting_details.count(),
                'total_quantity': total_quantity,
                'total_numeros_serie': total_numeros_serie,
                'created_at': counting.created_at,
                'updated_at': counting.updated_at
            }
            
        except Counting.DoesNotExist:
            logger.warning(f"Comptage avec l'ID {counting_id} non trouvé")
            return {}
