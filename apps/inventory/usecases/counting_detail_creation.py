"""
Use case pour la création de CountingDetail et NumeroSerie.
"""

import logging
from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import transaction
from ..models import CountingDetail, NSerie, Counting, JobDetail
from ..exceptions import (
    CountingDetailValidationError,
    ProductPropertyValidationError,
    CountingAssignmentValidationError,
    JobDetailValidationError,
    NumeroSerieValidationError,
    CountingModeValidationError
)
from apps.masterdata.models import Product, Location

logger = logging.getLogger(__name__)

class CountingDetailCreationUseCase:
    """
    Use case pour créer un CountingDetail et ses NumeroSerie associés.
    
    Ce use case gère :
    - Validation des données selon le mode de comptage
    - Création du CountingDetail
    - Création des NumeroSerie si nécessaire
    - Mise à jour du statut du JobDetail
    """
    
    def __init__(self):
        pass
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute la création complète du CountingDetail et NumeroSerie.
        
        Args:
            data: Données du comptage détaillé
            
        Returns:
            Dict[str, Any]: Résultat de la création
            
        Raises:
            CountingValidationError: Si les données sont invalides
        """
        try:
            with transaction.atomic():
                # ÉTAPE 1: Validation des données
                self._validate_data(data)
                
                # ÉTAPE 2: Récupération des objets existants
                counting, location, product, assignment, job_detail = self._get_related_objects(data)
                
                # ÉTAPE 3: Création du CountingDetail
                counting_detail = self._create_counting_detail(data, counting, location, product)
                
                # ÉTAPE 4: Création des NumeroSerie si nécessaire
                numeros_serie = self._create_numeros_serie(data, counting_detail)
                
                # ÉTAPE 5: Mise à jour du statut du JobDetail
                job_detail = self._update_job_detail_status(data, job_detail)
                
                return self._format_response(counting_detail, numeros_serie, job_detail)
                
        except Exception as e:
            logger.error(f"Erreur dans CountingDetailCreationUseCase.execute: {str(e)}", exc_info=True)
            raise
    
    def _validate_data(self, data: Dict[str, Any]) -> None:
        """
        Valide les données du comptage détaillé.
        
        Args:
            data: Données à valider
            
        Raises:
            CountingValidationError: Si les données sont invalides
        """
        errors = []
        
        # Champs obligatoires
        required_fields = ['counting_id', 'location_id', 'quantity_inventoried', 'assignment_id']
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Le champ '{field}' est obligatoire")
        
        # Validation de la quantité
        if 'quantity_inventoried' in data:
            try:
                quantity = int(data['quantity_inventoried'])
                if quantity <= 0:
                    errors.append("La quantité inventoriée doit être positive")
            except (ValueError, TypeError):
                errors.append("La quantité inventoriée doit être un nombre entier")
        
        # Validation selon le mode de comptage
        if 'counting_id' in data:
            try:
                counting = Counting.objects.get(id=data['counting_id'])
                self._validate_counting_mode_rules(counting, data, errors)
            except Counting.DoesNotExist:
                errors.append(f"Comptage avec l'ID {data['counting_id']} non trouvé")
        
        if errors:
            raise CountingDetailValidationError(" | ".join(errors))
    
    def _validate_counting_mode_rules(self, counting: Counting, data: Dict[str, Any], errors: List[str]) -> None:
        """
        Valide les règles selon le mode de comptage.
        
        Args:
            counting: L'objet Counting
            data: Données à valider
            errors: Liste des erreurs à remplir
        """
        count_mode = counting.count_mode
        
        if count_mode == "en vrac":
            # En vrac : article non obligatoire
            pass
        elif count_mode == "par article":
            # Par article : article obligatoire
            if not data.get('product_id'):
                errors.append("Le produit est obligatoire pour le mode de comptage 'par article'")
            else:
                # Vérifier les propriétés de l'article et valider les champs correspondants
                self._validate_product_properties(data, errors)
        elif count_mode == "image de stock":
            # Image de stock : article non obligatoire
            pass
        else:
            errors.append(f"Mode de comptage non supporté: {count_mode}")
        
        # Validation des numéros de série si activés
        if counting.n_serie and data.get('numeros_serie'):
            numeros_serie = data['numeros_serie']
            if not isinstance(numeros_serie, list):
                errors.append("Les numéros de série doivent être une liste")
            else:
                for i, ns in enumerate(numeros_serie):
                    if not isinstance(ns, dict) or 'n_serie' not in ns:
                        errors.append(f"Numéro de série {i+1}: format invalide")
                    elif not ns['n_serie']:
                        errors.append(f"Numéro de série {i+1}: valeur requise")
    
    def _validate_product_properties(self, data: Dict[str, Any], errors: List[str]) -> None:
        """
        Valide les propriétés de l'article et les champs correspondants.
        
        Args:
            data: Données à valider
            errors: Liste des erreurs à remplir
        """
        try:
            from apps.masterdata.models import Product
            product = Product.objects.get(id=data['product_id'])
            
            # Vérifier DLC - null n'est pas accepté si dlc=True
            if product.dlc and (data.get('dlc') is None or data.get('dlc') == ''):
                errors.append("Le produit nécessite une DLC (Date Limite de Consommation) - null n'est pas accepté")
            
            # Vérifier n_lot - null n'est pas accepté si n_lot=True
            if product.n_lot and (data.get('n_lot') is None or data.get('n_lot') == ''):
                errors.append("Le produit nécessite un numéro de lot - null n'est pas accepté")
            
            # Vérifier n_serie - null n'est pas accepté si n_serie=True
            if product.n_serie and (data.get('numeros_serie') is None or data.get('numeros_serie') == []):
                errors.append("Le produit nécessite des numéros de série - null n'est pas accepté")
            
            # Validation supplémentaire pour les numéros de série
            if product.n_serie and data.get('numeros_serie'):
                numeros_serie = data['numeros_serie']
                if not isinstance(numeros_serie, list) or len(numeros_serie) == 0:
                    errors.append("Le produit nécessite au moins un numéro de série")
                else:
                    for i, ns in enumerate(numeros_serie):
                        if not isinstance(ns, dict) or 'n_serie' not in ns:
                            errors.append(f"Numéro de série {i+1}: format invalide")
                        elif not ns['n_serie'] or ns['n_serie'] == '':
                            errors.append(f"Numéro de série {i+1}: valeur requise")
                        else:
                            # Vérifier que le numéro de série existe dans masterdata.NSerie pour ce produit
                            if not self._is_nserie_exists_in_masterdata(ns['n_serie'], product.id):
                                errors.append(f"Numéro de série {ns['n_serie']} n'existe pas dans masterdata pour ce produit")
                            # Vérifier aussi qu'il n'est pas déjà utilisé dans les CountingDetail
                            elif self._is_nserie_already_used(ns['n_serie'], product.id):
                                errors.append(f"Numéro de série {ns['n_serie']} déjà utilisé pour ce produit")
            
        except Product.DoesNotExist:
            errors.append(f"Produit avec l'ID {data['product_id']} non trouvé")
        except Exception as e:
            errors.append(f"Erreur lors de la validation du produit: {str(e)}")
    
    def _is_nserie_already_used(self, n_serie: str, product_id: int) -> bool:
        """
        Vérifie si un numéro de série est déjà utilisé pour un produit.
        
        Args:
            n_serie: Le numéro de série à vérifier
            product_id: L'ID du produit
            
        Returns:
            bool: True si le numéro de série est déjà utilisé
        """
        try:
            # Vérifier dans les CountingDetail existants
            from ..models import CountingDetail, NSerie
            
            # Chercher dans les NSerie existants pour ce produit
            existing_nserie = NSerie.objects.filter(
                counting_detail__product_id=product_id,
                n_serie=n_serie
            ).exists()
            
            if existing_nserie:
                return True
            
            # Note: masterdata.NSerie contient les numéros de série VALIDES, pas utilisés
            # On ne vérifie que dans inventory.NSerie pour la duplication
            
            return False
            
        except Exception as e:
            # En cas d'erreur, on considère que c'est déjà utilisé pour la sécurité
            return True
    
    def _is_nserie_exists_in_masterdata(self, n_serie: str, product_id: int) -> bool:
        """
        Vérifie si un numéro de série existe dans masterdata.NSerie pour un produit.
        
        Args:
            n_serie: Le numéro de série à vérifier
            product_id: L'ID du produit
            
        Returns:
            bool: True si le numéro de série existe
        """
        try:
            from apps.masterdata.models import NSerie as MasterNSerie
            return MasterNSerie.objects.filter(
                product_id=product_id,
                n_serie=n_serie
            ).exists()
        except:
            return False
    
    def _get_related_objects(self, data: Dict[str, Any]) -> tuple:
        """
        Récupère tous les objets liés nécessaires.
        
        Args:
            data: Données de la requête
            
        Returns:
            tuple: (counting, location, product, assignment, job_detail)
        """
        # Récupérer le comptage
        try:
            counting = Counting.objects.get(id=data['counting_id'])
        except Counting.DoesNotExist:
            raise CountingDetailValidationError(f"Comptage avec l'ID {data['counting_id']} non trouvé")
        
        # Récupérer l'emplacement
        try:
            from apps.masterdata.models import Location
            location = Location.objects.get(id=data['location_id'])
        except Location.DoesNotExist:
            raise CountingDetailValidationError(f"Emplacement avec l'ID {data['location_id']} non trouvé")
        
        # Récupérer le produit (optionnel selon le mode)
        product = None
        if data.get('product_id'):
            try:
                from apps.masterdata.models import Product
                product = Product.objects.get(id=data['product_id'])
            except Product.DoesNotExist:
                raise CountingDetailValidationError(f"Produit avec l'ID {data['product_id']} non trouvé")
        
        # Récupérer l'assignment
        try:
            from ..models import Assigment
            assignment = Assigment.objects.get(id=data['assignment_id'])
        except Assigment.DoesNotExist:
            raise CountingDetailValidationError(f"Assignment avec l'ID {data['assignment_id']} non trouvé")
        
        # Récupérer le job_detail associé à cet assignment
        try:
            # Utiliser filter().first() au lieu de get() pour éviter l'erreur de multiple objets
            job_detail = JobDetail.objects.filter(
                job=assignment.job, 
                counting=counting
            ).first()
            
            if not job_detail:
                raise CountingDetailValidationError(f"JobDetail non trouvé pour l'assignment {data['assignment_id']} et le comptage {data['counting_id']}")
                
        except Exception as e:
            if "more than one" in str(e):
                # Cas spécial : plusieurs JobDetail trouvés
                logger.warning(f"Plusieurs JobDetail trouvés pour job={assignment.job.id} et counting={counting.id}")
                
                # Prendre le premier ou le plus récent
                job_detail = JobDetail.objects.filter(
                    job=assignment.job, 
                    counting=counting
                ).order_by('-created_at').first()
                
                if not job_detail:
                    raise CountingDetailValidationError(f"Impossible de déterminer le JobDetail pour l'assignment {data['assignment_id']} et le comptage {data['counting_id']}")
                    
                logger.info(f"JobDetail sélectionné: {job_detail.id}")
            else:
                raise CountingDetailValidationError(f"Erreur lors de la récupération du JobDetail: {str(e)}")
        
        return counting, location, product, assignment, job_detail
    
    def _create_counting_detail(self, data: Dict[str, Any], counting: Counting, 
                               location: Location, product: Optional[Product]) -> CountingDetail:
        """
        Crée le CountingDetail.
        
        Args:
            data: Données du comptage
            counting: L'objet Counting
            location: L'objet Location
            product: L'objet Product (optionnel)
            
        Returns:
            CountingDetail: L'objet créé
        """
        counting_detail = CountingDetail(
            quantity_inventoried=data['quantity_inventoried'],
            product=product,
            dlc=data.get('dlc'),
            n_lot=data.get('n_lot'),
            location=location,
            counting=counting,
            last_synced_at=timezone.now()
        )
        
        # Générer la référence
        counting_detail.reference = counting_detail.generate_reference(counting_detail.REFERENCE_PREFIX)
        
        # Sauvegarder
        counting_detail.save()
        
        logger.info(f"CountingDetail {counting_detail.id} créé pour le comptage {counting.id}")
        
        return counting_detail
    
    def _create_numeros_serie(self, data: Dict[str, Any], counting_detail: CountingDetail) -> List[NSerie]:
        """
        Crée les NumeroSerie si nécessaire.
        
        Args:
            data: Données du comptage
            counting_detail: Le CountingDetail créé
            
        Returns:
            List[NSerie]: Liste des NumeroSerie créés
        """
        numeros_serie = []
        
        # Créer les numéros de série si fournis dans la requête, peu importe la configuration du comptage
        if data.get('numeros_serie'):
            for ns_data in data['numeros_serie']:
                nserie = NSerie(
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
                        numeros_serie: List[NSerie], 
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
        response = {
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
                    'reference': ns.reference,
                    'n_serie': ns.n_serie
                } for ns in numeros_serie
            ],
            'job_detail': {
                'id': job_detail.id,
                'status': job_detail.status,
                'updated_at': job_detail.updated_at
            },
            'message': f'CountingDetail créé avec {len(numeros_serie)} numéro(s) de série et JobDetail mis à jour vers {job_detail.status}'
        }
        
        return response
