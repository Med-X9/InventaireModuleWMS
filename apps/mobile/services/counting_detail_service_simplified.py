"""
Service simplifié pour la gestion des CountingDetail et NumeroSerie dans l'app mobile.
Utilise le CountingDetailCreationUseCase existant.
"""
from typing import Dict, Any, List, Optional
from django.db import transaction
from apps.inventory.models import CountingDetail
from apps.inventory.usecases.counting_detail_creation import CountingDetailCreationUseCase
import logging

logger = logging.getLogger(__name__)

class CountingDetailService:
    """
    Service simplifié pour la gestion des CountingDetail et NumeroSerie dans l'app mobile.
    
    Ce service utilise le CountingDetailCreationUseCase existant pour éviter la duplication de code.
    """
    
    def __init__(self):
        self.usecase = CountingDetailCreationUseCase()
    
    def create_counting_detail(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un CountingDetail et ses NumeroSerie associés en utilisant le use case.
        
        Args:
            data: Données du comptage détaillé
            
        Returns:
            Dict[str, Any]: Résultat de la création
            
        Raises:
            CountingDetailValidationError: Si les données sont invalides
        """
        try:
            logger.info(f"Création d'un CountingDetail avec les données: {data}")
            
            # Utiliser le use case existant
            result = self.usecase.execute(data)
            
            logger.info(f"CountingDetail créé avec succès via use case")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du CountingDetail: {str(e)}")
            raise e
    
    def create_counting_details_batch(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crée plusieurs CountingDetail et leurs NumeroSerie associés en lot.
        Utilise une transaction pour s'assurer que soit tout réussit, soit rien n'est enregistré.
        
        Args:
            data_list: Liste des données de comptage détaillé
            
        Returns:
            Dict[str, Any]: Résultat de la création en lot
        """
        try:
            logger.info(f"Création en lot de {len(data_list)} CountingDetail")
            
            results = []
            errors = []
            
            # Utiliser une transaction pour s'assurer que tout réussit ou rien
            with transaction.atomic():
                for i, data in enumerate(data_list):
                    try:
                        # Vérifier si l'enregistrement existe déjà
                        existing_detail = self._find_existing_counting_detail(data)
                        
                        if existing_detail:
                            # Modifier l'enregistrement existant
                            result = self._update_counting_detail(existing_detail, data)
                            result['action'] = 'updated'
                        else:
                            # Créer un nouvel enregistrement en utilisant le use case
                            result = self.create_counting_detail(data)
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
                        
                        # Si il y a une erreur, la transaction sera automatiquement annulée
                        logger.error(f"Erreur détectée à l'index {i}, annulation de toute la transaction")
                        raise e  # Cela va déclencher un rollback de la transaction
            
            # Si on arrive ici, tout a réussi
            return {
                'success': True,
                'total_processed': len(data_list),
                'successful': len(results),
                'failed': 0,
                'results': results,
                'errors': []
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la création en lot: {str(e)}")
            return {
                'success': False,
                'total_processed': len(data_list),
                'successful': 0,
                'failed': len(errors) if errors else 1,
                'results': [],
                'errors': errors if errors else [{'index': 0, 'data': data_list[0] if data_list else {}, 'error': str(e)}],
                'message': f"Transaction annulée à cause d'une erreur: {str(e)}"
            }
    
    def validate_counting_details_batch(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Valide plusieurs CountingDetail sans les créer.
        
        Args:
            data_list: Liste des données de comptage détaillé
            
        Returns:
            Dict[str, Any]: Résultat de la validation
        """
        try:
            logger.info(f"Validation en lot de {len(data_list)} CountingDetail")
            
            results = []
            errors = []
            
            for i, data in enumerate(data_list):
                try:
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
                    
                    # ARRÊTER la validation dès qu'il y a une erreur
                    logger.error(f"Validation arrêtée à l'index {i} à cause d'une erreur")
                    break
            
            # Si il y a des erreurs, considérer la validation comme échouée
            if errors:
                return {
                    'success': False,
                    'total_processed': len(data_list),
                    'valid': len(results),
                    'invalid': len(errors),
                    'results': results,
                    'errors': errors,
                    'message': f"Validation arrêtée à l'index {errors[0]['index']} à cause d'une erreur"
                }
            
            return {
                'success': True,
                'total_processed': len(data_list),
                'valid': len(results),
                'invalid': 0,
                'results': results,
                'errors': []
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation en lot: {str(e)}")
            return {
                'success': False,
                'total_processed': len(data_list),
                'valid': 0,
                'invalid': len(errors) if errors else 1,
                'results': [],
                'errors': errors if errors else [{'index': 0, 'data': data_list[0] if data_list else {}, 'error': str(e)}],
                'message': f"Erreur lors de la validation: {str(e)}"
            }
    
    def _find_existing_counting_detail(self, data: Dict[str, Any]) -> Optional[CountingDetail]:
        """
        Recherche un CountingDetail existant basé sur les critères de matching.
        
        Args:
            data: Données du comptage détaillé
            
        Returns:
            Optional[CountingDetail]: Le CountingDetail existant ou None
        """
        try:
            return CountingDetail.objects.filter(
                counting_id=data['counting_id'],
                location_id=data['location_id'],
                product_id=data['product_id']
            ).first()
        except Exception as e:
            logger.error(f"Erreur lors de la recherche d'un CountingDetail existant: {str(e)}")
            return None
    
    def _update_counting_detail(self, counting_detail: CountingDetail, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un CountingDetail existant.
        
        Args:
            counting_detail: Le CountingDetail à mettre à jour
            data: Nouvelles données
            
        Returns:
            Dict[str, Any]: Résultat de la mise à jour
        """
        try:
            # Mettre à jour les champs principaux
            counting_detail.quantity_inventoried = data['quantity_inventoried']
            if 'dlc' in data:
                counting_detail.dlc = data['dlc']
            if 'n_lot' in data:
                counting_detail.n_lot = data['n_lot']
            
            counting_detail.save()
            
            # Mettre à jour les NumeroSerie si fournis
            numeros_serie = []
            if 'numeros_serie' in data and data['numeros_serie']:
                # Supprimer les anciens NumeroSerie
                counting_detail.numeros_serie.all().delete()
                
                # Créer les nouveaux NumeroSerie
                from apps.inventory.models import NSerieInventory
                for n_serie_data in data['numeros_serie']:
                    n_serie = NSerieInventory.objects.create(
                        reference=NSerieInventory.generate_reference(),
                        n_serie=n_serie_data['n_serie'],
                        counting_detail=counting_detail
                    )
                    numeros_serie.append({
                        'id': n_serie.id,
                        'n_serie': n_serie.n_serie,
                        'reference': n_serie.reference
                    })
            
            return {
                'counting_detail': {
                    'id': counting_detail.id,
                    'reference': counting_detail.reference,
                    'quantity_inventoried': counting_detail.quantity_inventoried,
                    'product_id': counting_detail.product.id,
                    'location_id': counting_detail.location.id,
                    'counting_id': counting_detail.counting.id,
                    'created_at': counting_detail.created_at,
                    'updated_at': counting_detail.updated_at
                },
                'numeros_serie': numeros_serie
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du CountingDetail: {str(e)}")
            raise e
