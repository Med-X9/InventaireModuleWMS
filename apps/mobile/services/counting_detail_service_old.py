"""
Service pour la gestion des CountingDetail et NumeroSerie dans l'app mobile.
"""
from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import transaction
from apps.inventory.models import CountingDetail, NSerieInventory, Counting, JobDetail
from apps.inventory.exceptions import (
    CountingDetailValidationError,
    ProductPropertyValidationError,
    CountingAssignmentValidationError,
    JobDetailValidationError,
    NumeroSerieValidationError,
    CountingModeValidationError
)
from apps.inventory.usecases.counting_detail_creation import CountingDetailCreationUseCase
from apps.masterdata.models import Product, Location
import logging

logger = logging.getLogger(__name__)

class CountingDetailService:
    """
    Service pour la gestion des CountingDetail et NumeroSerie dans l'app mobile.
    
    Ce service gère :
    - Création de CountingDetail individuels et en lot
    - Validation de CountingDetail individuels et en lot
    - Création des NumeroSerie associés
    - Mise à jour des statuts des JobDetail
    - Détection et mise à jour des enregistrements existants
    """
    
    def __init__(self):
        self.usecase = CountingDetailCreationUseCase()
    
    def create_counting_detail(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un CountingDetail et ses NumeroSerie associés.
        
        Args:
            data: Données du comptage détaillé
            
        Returns:
            Dict[str, Any]: Résultat de la création
            
        Raises:
            CountingDetailValidationError: Si les données sont invalides
        """
        try:
            logger.info(f"Création d'un CountingDetail avec les données: {data}")
            
            # Utiliser le use case existant au lieu de réécrire la logique
            result = self.usecase.execute(data)
            
            logger.info(f"CountingDetail créé avec succès via use case")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du CountingDetail: {str(e)}")
            raise
    
    def create_counting_details_batch(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crée plusieurs CountingDetail et leurs NumeroSerie associés en lot.
        Utilise une transaction pour s'assurer que soit tout réussit, soit rien n'est enregistré.
        
        Args:
            data_list: Liste des données de comptage détaillé
            
        Returns:
            Dict[str, Any]: Résultat de la création en lot
        """
        from django.db import transaction
        
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
                            # Créer un nouvel enregistrement
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
            # La transaction a été automatiquement annulée
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
                    self._validate_data(data)
                    
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
                'invalid': len(errors),
                'results': results,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation en lot: {str(e)}")
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
                numeros_serie = self._create_numeros_serie(data, counting_detail)
            
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
    
    def _validate_data(self, data: Dict[str, Any]) -> None:
        """
        Valide les données d'un comptage.
        
        Args:
            data: Données à valider
            
        Raises:
            CountingDetailValidationError: Si les données sont invalides
        """
        # Vérifier les champs obligatoires
        required_fields = ['counting_id', 'location_id', 'quantity_inventoried', 'assignment_id']
        for field in required_fields:
            if field not in data:
                raise CountingDetailValidationError(f"Le champ '{field}' est obligatoire")
        
        # Vérifier que quantity_inventoried est un entier positif
        if not isinstance(data['quantity_inventoried'], int) or data['quantity_inventoried'] < 0:
            raise CountingDetailValidationError("La quantité inventoriée doit être un entier positif")
    
    def _get_related_objects(self, data: Dict[str, Any]) -> tuple:
        """
        Récupère les objets liés nécessaires.
        
        Args:
            data: Données du comptage
            
        Returns:
            tuple: (counting, location, product, assignment, job_detail)
        """
        try:
            # Récupérer le comptage
            counting = Counting.objects.get(id=data['counting_id'])
            
            # Récupérer l'emplacement
            location = Location.objects.get(id=data['location_id'])
            
            # Récupérer le produit si fourni
            product = None
            if data.get('product_id'):
                product = Product.objects.get(id=data['product_id'])
            
            # Récupérer l'assignment et le job_detail
            from apps.inventory.models import Assigment, JobDetail
            assignment = Assigment.objects.get(id=data['assignment_id'])
            
            # Récupérer le job_detail associé à cet assignment
            job_detail = JobDetail.objects.filter(
                job=assignment.job, 
                counting=counting
            ).first()
            
            if not job_detail:
                raise CountingDetailValidationError(f"JobDetail non trouvé pour l'assignment {data['assignment_id']} et le comptage {data['counting_id']}")
            
            return counting, location, product, assignment, job_detail
            
        except Counting.DoesNotExist:
            raise CountingDetailValidationError(f"Comptage avec l'ID {data['counting_id']} non trouvé")
        except Location.DoesNotExist:
            raise CountingDetailValidationError(f"Emplacement avec l'ID {data['location_id']} non trouvé")
        except Product.DoesNotExist:
            raise CountingDetailValidationError(f"Produit avec l'ID {data['product_id']} non trouvé")
        except Exception as e:
            raise CountingDetailValidationError(f"Erreur lors de la récupération des objets liés: {str(e)}")
    
    def _create_counting_detail(self, data: Dict[str, Any], counting: Counting, 
                               location: Location, product: Optional[Product]) -> CountingDetail:
        """
        Crée un CountingDetail.
        
        Args:
            data: Données du comptage
            counting: Objet Counting
            location: Objet Location
            product: Objet Product (optionnel)
            
        Returns:
            CountingDetail: Le CountingDetail créé
        """
        counting_detail = CountingDetail(
            quantity_inventoried=data['quantity_inventoried'],
            product=product,
            location=location,
            counting=counting,
            dlc=data.get('dlc'),
            n_lot=data.get('n_lot')
        )
        
        # Générer la référence
        counting_detail.reference = counting_detail.generate_reference(counting_detail.REFERENCE_PREFIX)
        
        # Sauvegarder
        counting_detail.save()
        
        logger.info(f"CountingDetail {counting_detail.id} créé pour le comptage {counting.id}")
        
        return counting_detail
    
    def _create_numeros_serie(self, data: Dict[str, Any], counting_detail: CountingDetail) -> List[NSerieInventory]:
        """
        Crée les NumeroSerie si nécessaire.
        
        Args:
            data: Données du comptage
            counting_detail: Le CountingDetail créé
            
        Returns:
            List[NSerieInventory]: Liste des NumeroSerie créés
        """
        numeros_serie = []
        
        # Créer les numéros de série si fournis dans la requête
        if data.get('numeros_serie'):
            for ns_data in data['numeros_serie']:
                nserie = NSerieInventory(
                    n_serie=ns_data['n_serie'],
                    counting_detail=counting_detail
                )
                
                # Générer la référence
                nserie.reference = nserie.generate_reference(nserie.REFERENCE_PREFIX)
                
                # Sauvegarder
                nserie.save()
                
                numeros_serie.append(nserie)
                
                logger.info(f"NumeroSerie {nserie.id} créé pour le CountingDetail {counting_detail.id}")
        
        return numeros_serie
    
    def _update_job_detail_status(self, data: Dict[str, Any], job_detail: JobDetail) -> JobDetail:
        """
        Met à jour le statut du JobDetail associé.
        
        Args:
            data: Données du comptage
            job_detail: Le JobDetail à mettre à jour
            
        Returns:
            JobDetail: Le JobDetail mis à jour
        """
        # Mettre à jour le statut vers TERMINE
        job_detail.status = 'TERMINE'
        job_detail.termine_date = timezone.now()
        job_detail.save()
        
        logger.info(f"JobDetail {job_detail.id} mis à jour vers TERMINE")
        
        return job_detail
    
    def _format_response(self, counting_detail: CountingDetail, 
                        numeros_serie: List[NSerieInventory], 
                        job_detail: JobDetail) -> Dict[str, Any]:
        """
        Formate la réponse de l'API.
        
        Args:
            counting_detail: Le CountingDetail créé
            numeros_serie: Liste des NumeroSerie créés
            job_detail: Le JobDetail mis à jour
            
        Returns:
            Dict[str, Any]: Réponse formatée
        """
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
            ],
            'job_detail': {
                'id': job_detail.id,
                'status': job_detail.status,
                'termine_date': job_detail.termine_date
            }
        }
