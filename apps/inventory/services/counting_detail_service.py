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
    
    def create_counting_details_batch(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crée plusieurs CountingDetail et leurs NumeroSerie associés en lot.
        
        Args:
            data_list: Liste des données de comptage détaillé
            
        Returns:
            Dict[str, Any]: Résultat de la création en lot
        """
        try:
            logger.info(f"Création en lot de {len(data_list)} CountingDetail")
            
            results = []
            errors = []
            
            for i, data in enumerate(data_list):
                try:
                    # Vérifier si l'enregistrement existe déjà
                    existing_detail = self._find_existing_counting_detail(data)
                    
                    if existing_detail:
                        # Modifier l'enregistrement existant
                        result = self._update_counting_detail(existing_detail, data)
                        result['action'] = 'updated'
                    else:
                        # Créer un nouvel enregistrement
                        result = self.use_case.execute(data)
                        result['action'] = 'created'
                    
                    results.append({
                        'index': i,
                        'data': data,
                        'result': result
                    })
                    
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de l'enregistrement {i}: {str(e)}")
                    errors.append({
                        'index': i,
                        'data': data,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'total_processed': len(data_list),
                'successful': len(results),
                'failed': len(errors),
                'results': results,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la création en lot: {str(e)}")
            raise
    
    def validate_counting_details_batch(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Valide plusieurs CountingDetail sans les créer.
        
        Args:
            data_list: Liste des données à valider
            
        Returns:
            Dict[str, Any]: Résultat de la validation
        """
        try:
            logger.info(f"Validation en lot de {len(data_list)} CountingDetail")
            
            results = []
            errors = []
            
            for i, data in enumerate(data_list):
                try:
                    # Valider les données
                    validation_result = self.use_case._validate_data(data)
                    
                    # Vérifier si l'enregistrement existe
                    existing_detail = self._find_existing_counting_detail(data)
                    
                    results.append({
                        'index': i,
                        'data': data,
                        'valid': True,
                        'exists': existing_detail is not None,
                        'existing_id': existing_detail.id if existing_detail else None,
                        'action_needed': 'update' if existing_detail else 'create'
                    })
                    
                except Exception as e:
                    logger.error(f"Erreur de validation pour l'enregistrement {i}: {str(e)}")
                    errors.append({
                        'index': i,
                        'data': data,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'total_processed': len(data_list),
                'valid': len(results),
                'invalid': len(errors),
                'results': results,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation en lot: {str(e)}")
            raise
    
    def _find_existing_counting_detail(self, data: Dict[str, Any]) -> Optional[CountingDetail]:
        """
        Recherche un CountingDetail existant basé sur les critères de matching.
        
        Args:
            data: Données du comptage
            
        Returns:
            Optional[CountingDetail]: CountingDetail existant ou None
        """
        try:
            # Critères de recherche pour trouver un enregistrement existant
            # Combinaison counting + location + product (si fourni)
            filters = {
                'counting_id': data.get('counting_id'),
                'location_id': data.get('location_id')
            }
            
            # Ajouter le produit si fourni
            if data.get('product_id'):
                filters['product_id'] = data.get('product_id')
            
            # Rechercher l'enregistrement existant
            existing = CountingDetail.objects.filter(**filters).first()
            
            return existing
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche d'enregistrement existant: {str(e)}")
            return None
    
    def _update_counting_detail(self, counting_detail: CountingDetail, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un CountingDetail existant.
        
        Args:
            counting_detail: CountingDetail à mettre à jour
            data: Nouvelles données
            
        Returns:
            Dict[str, Any]: Résultat de la mise à jour
        """
        try:
            # Mettre à jour les champs
            if 'quantity_inventoried' in data:
                counting_detail.quantity_inventoried = data['quantity_inventoried']
            
            if 'dlc' in data:
                counting_detail.dlc = data.get('dlc')
            
            if 'n_lot' in data:
                counting_detail.n_lot = data.get('n_lot')
            
            # Sauvegarder les modifications
            counting_detail.save()
            
            # Mettre à jour les numéros de série si fournis
            numeros_serie = []
            if data.get('numeros_serie'):
                # Supprimer les anciens numéros de série
                NSerieInventory.objects.filter(counting_detail=counting_detail).delete()
                
                # Créer les nouveaux
                numeros_serie = self.use_case._create_numeros_serie(data, counting_detail)
            
            logger.info(f"CountingDetail {counting_detail.id} mis à jour avec succès")
            
            return {
                'counting_detail': {
                    'id': counting_detail.id,
                    'reference': counting_detail.reference,
                    'quantity_inventoried': counting_detail.quantity_inventoried,
                    'product_id': counting_detail.product.id if counting_detail.product else None,
                    'location_id': counting_detail.location.id,
                    'counting_id': counting_detail.counting.id,
                    'created_at': counting_detail.created_at,
                    'updated_at': counting_detail.updated_at
                },
                'numeros_serie': [
                    {
                        'id': ns.id,
                        'n_serie': ns.n_serie,
                        'reference': ns.reference
                    } for ns in numeros_serie
                ]
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du CountingDetail: {str(e)}")
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
