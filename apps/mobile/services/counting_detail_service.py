"""
Service pour la gestion des CountingDetail et NumeroSerie dans l'app mobile.
Utilise le CountingDetailCreationUseCase existant.
"""
from typing import Dict, Any, List, Optional
from django.db import transaction
from apps.inventory.models import CountingDetail, Assigment, Job
from apps.inventory.usecases.counting_detail_creation import CountingDetailCreationUseCase
from apps.mobile.exceptions import CountingAssignmentValidationError
import logging

logger = logging.getLogger(__name__)

class CountingDetailService:
    """
    Service pour la gestion des CountingDetail et NumeroSerie dans l'app mobile.
    
    Ce service utilise le CountingDetailCreationUseCase existant pour éviter la duplication de code.
    """
    
    def __init__(self):
        self.usecase = CountingDetailCreationUseCase()
    
    def validate_assignments_belong_to_job(self, job_id: int, assignment_ids: list) -> None:
        """
        Vérifie que tous les assignment_id appartiennent au job_id spécifié.
        
        Args:
            job_id: L'ID du job depuis l'URL
            assignment_ids: Liste des IDs d'assignments à vérifier
            
        Raises:
            CountingAssignmentValidationError: Si un assignment n'appartient pas au job
        """
        if not assignment_ids:
            return
        
        # Vérifier que le job existe
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise CountingAssignmentValidationError(f"Job avec l'ID {job_id} non trouvé")
        
        # Récupérer tous les assignments du job
        job_assignments = Assigment.objects.filter(job_id=job_id).values_list('id', flat=True)
        job_assignment_ids = set(job_assignments)
        
        # Vérifier que tous les assignment_ids fournis appartiennent au job
        invalid_assignments = []
        for assignment_id in assignment_ids:
            if assignment_id not in job_assignment_ids:
                invalid_assignments.append(assignment_id)
        
        if invalid_assignments:
            raise CountingAssignmentValidationError(
                f"Les assignments suivants n'appartiennent pas au job {job_id}: {invalid_assignments}"
            )
    
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
            
            # Le use case fait déjà toute la validation nécessaire
            result = self.usecase.execute(data)
            
            logger.info("CountingDetail créé avec succès via use case")
            
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
            
            # Extraire l'expression conditionnelle imbriquée
            if errors:
                error_list = errors
            else:
                error_list = [{'index': 0, 'data': data_list[0] if data_list else {}, 'error': str(e)}]
            
            return {
                'success': False,
                'total_processed': len(data_list),
                'successful': 0,
                'failed': len(errors) if errors else 1,
                'results': [],
                'errors': error_list,
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
                validation_result = self._validate_single_counting_detail(i, data)
                if validation_result['success']:
                    results.append(validation_result['result'])
                else:
                    errors.append(validation_result['error'])
                    logger.error(f"Validation arrêtée à l'index {i} à cause d'une erreur")
                    break
            
            return self._build_validation_response(data_list, results, errors)
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation en lot: {str(e)}")
            return self._build_error_response(data_list, errors, e)
    
    def _validate_single_counting_detail(self, index: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide un seul CountingDetail.
        
        Args:
            index: Index de l'élément dans la liste
            data: Données du comptage détaillé
            
        Returns:
            Dict[str, Any]: Résultat de la validation
        """
        try:
            # La validation complète sera faite par le use case lors de la création
            existing_detail = self._find_existing_counting_detail(data)
            
            return {
                'success': True,
                'result': {
                    'index': index,
                    'data': data,
                    'valid': True,
                    'exists': existing_detail is not None,
                    'existing_id': existing_detail.id if existing_detail else None,
                    'action_needed': 'update' if existing_detail else 'create'
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur de validation pour l'enregistrement {index}: {str(e)}")
            return {
                'success': False,
                'error': {
                    'index': index,
                    'data': data,
                    'error': str(e)
                }
            }
    
    def _build_validation_response(self, data_list: List[Dict[str, Any]], results: List[Dict], errors: List[Dict]) -> Dict[str, Any]:
        """
        Construit la réponse de validation.
        
        Args:
            data_list: Liste originale des données
            results: Liste des résultats de validation
            errors: Liste des erreurs
            
        Returns:
            Dict[str, Any]: Réponse de validation
        """
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
    
    def _build_error_response(self, data_list: List[Dict[str, Any]], errors: List[Dict], exception: Exception) -> Dict[str, Any]:
        """
        Construit la réponse d'erreur.
        
        Args:
            data_list: Liste originale des données
            errors: Liste des erreurs existantes
            exception: Exception levée
            
        Returns:
            Dict[str, Any]: Réponse d'erreur
        """
        if errors:
            error_list = errors
        else:
            error_list = [{'index': 0, 'data': data_list[0] if data_list else {}, 'error': str(exception)}]
        
        return {
            'success': False,
            'total_processed': len(data_list),
            'valid': 0,
            'invalid': len(errors) if errors else 1,
            'results': [],
            'errors': error_list,
            'message': f"Erreur lors de la validation: {str(exception)}"
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
                from apps.inventory.models import NSerieInventory
                NSerieInventory.objects.filter(counting_detail=counting_detail).delete()
                
                # Créer les nouveaux NumeroSerie
                for n_serie_data in data['numeros_serie']:
                    n_serie = NSerieInventory.objects.create(
                        n_serie=n_serie_data['n_serie'],
                        counting_detail=counting_detail
                    )
                    # Générer la référence après création
                    n_serie.reference = n_serie.generate_reference(n_serie.REFERENCE_PREFIX)
                    n_serie.save()
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
    
    def get_counting_details_by_counting(self, counting_id: int):
        """
        Récupère tous les CountingDetail d'un comptage.
        
        Args:
            counting_id: ID du comptage
            
        Returns:
            List[CountingDetail]: Liste des CountingDetail
        """
        try:
            from apps.inventory.models import Counting
            counting = Counting.objects.get(id=counting_id)
            return CountingDetail.objects.filter(counting=counting).order_by('-created_at')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des CountingDetail: {str(e)}")
            return []
    
    def get_counting_details_by_location(self, location_id: int):
        """
        Récupère tous les CountingDetail d'un emplacement.
        
        Args:
            location_id: ID de l'emplacement
            
        Returns:
            List[CountingDetail]: Liste des CountingDetail
        """
        try:
            return CountingDetail.objects.filter(location_id=location_id).order_by('-created_at')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des CountingDetail par emplacement: {str(e)}")
            return []
    
    def get_counting_details_by_product(self, product_id: int):
        """
        Récupère tous les CountingDetail d'un produit.
        
        Args:
            product_id: ID du produit
            
        Returns:
            List[CountingDetail]: Liste des CountingDetail
        """
        try:
            return CountingDetail.objects.filter(product_id=product_id).order_by('-created_at')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des CountingDetail par produit: {str(e)}")
            return []
    
    def get_numeros_serie_by_counting_detail(self, counting_detail_id: int):
        """
        Récupère tous les NumeroSerie d'un CountingDetail.
        
        Args:
            counting_detail_id: ID du CountingDetail
            
        Returns:
            List[NSerieInventory]: Liste des NumeroSerie
        """
        try:
            from apps.inventory.models import NSerieInventory
            counting_detail = CountingDetail.objects.get(id=counting_detail_id)
            return NSerieInventory.objects.filter(counting_detail=counting_detail)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des NumeroSerie: {str(e)}")
            return []
    
    def get_counting_summary(self, counting_id: int):
        """
        Récupère un résumé des comptages pour un comptage donné.
        
        Args:
            counting_id: ID du comptage
            
        Returns:
            Dict[str, Any]: Résumé des comptages
        """
        try:
            from apps.inventory.models import Counting, NSerieInventory
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
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du résumé: {str(e)}")
            return {}
