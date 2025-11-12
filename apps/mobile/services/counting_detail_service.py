"""
Service pour la gestion des CountingDetail et NumeroSerie dans l'app mobile.
Utilise le CountingDetailCreationUseCase existant.
"""
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.inventory.models import CountingDetail, Assigment, Job, EcartComptage, ComptageSequence, Inventory, Counting, JobDetail, NSerieInventory
from apps.inventory.usecases.counting_detail_creation import CountingDetailCreationUseCase
from apps.mobile.exceptions import CountingAssignmentValidationError, EcartComptageResoluError
from apps.masterdata.models import Product, Location
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
    
    def create_counting_detail(self, data: Dict[str, Any], job_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Crée un CountingDetail et ses NumeroSerie associés en utilisant le use case.
        
        Args:
            data: Données du comptage détaillé
            job_id: ID du job (optionnel, sera utilisé si fourni)
            
        Returns:
            Dict[str, Any]: Résultat de la création
            
        Raises:
            CountingDetailValidationError: Si les données sont invalides
        """
        try:
            logger.info(f"Création d'un CountingDetail avec les données: {data}")
            
            # Ajouter job_id aux données si fourni
            if job_id:
                data['job_id'] = job_id
            
            # Le use case fait déjà toute la validation nécessaire
            result = self.usecase.execute(data)
            
            logger.info("CountingDetail créé avec succès via use case")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du CountingDetail: {str(e)}")
            raise e
    
    def create_counting_details_batch(self, data_list: List[Dict[str, Any]], job_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Crée plusieurs CountingDetail et leurs NumeroSerie associés en lot.
        Détecte automatiquement ou crée des EcartComptage pour chaque CountingDetail
        basé sur product + location + inventory.
        Utilise une transaction pour s'assurer que soit tout réussit, soit rien n'est enregistré.
        OPTIMISÉ pour les performances avec préchargement des données.
        
        Args:
            data_list: Liste des données de comptage détaillé
            job_id: ID du job (optionnel, pour obtenir l'inventory_id)
            
        Returns:
            Dict[str, Any]: Résultat de la création en lot
            
        Raises:
            EcartComptageResoluError: Si on essaie d'ajouter un comptage à un écart résolu
        """
        try:
            logger.info(f"Création en lot de {len(data_list)} CountingDetail")
            
            results = []
            errors = []
            
            # Utiliser une transaction pour s'assurer que tout réussit ou rien
            with transaction.atomic():
                # OPTIMISATION 1: Précharger tous les CountingDetail existants en une seule requête
                existing_details_map = self._prefetch_existing_counting_details(data_list)
                
                # OPTIMISATION 2 NOUVELLE: Précharger tous les objets liés en une seule fois
                related_objects_cache = self._prefetch_all_related_objects(data_list)
                
                # OPTIMISATION 3 NOUVELLE: Valider tous les éléments en lot
                validation_results = self._validate_all_data_batch(data_list, related_objects_cache)
                invalid_items = [i for i, v in enumerate(validation_results) if not v.get('valid', False)]
                if invalid_items:
                    invalid_data = [data_list[i] for i in invalid_items]
                    errors.append({
                        'index': invalid_items[0],
                        'data': invalid_data[0],
                        'error': validation_results[invalid_items[0]].get('error', 'Validation échouée')
                    })
                    raise ValidationError(f"Validation échouée pour {len(invalid_items)} élément(s)")
                
                # OPTIMISATION 4 NOUVELLE: Créer tous les CountingDetail en bulk
                counting_details_to_process = []
                created_details = []
                
                # Séparer les éléments à créer et ceux à mettre à jour
                items_to_create = []
                items_to_update = []
                
                for i, data in enumerate(data_list):
                    existing_detail = existing_details_map.get(self._get_detail_key(data))
                    
                    if existing_detail:
                        items_to_update.append({
                            'index': i,
                            'detail': existing_detail,
                            'data': data
                        })
                    else:
                        items_to_create.append({
                            'index': i,
                            'data': data,
                            'related': validation_results[i]['related_objects']
                        })
                
                # Mettre à jour les existants
                for item in items_to_update:
                    try:
                        result = self._update_counting_detail(item['detail'], item['data'])
                        result['action'] = 'updated'
                        counting_details_to_process.append({
                            'index': item['index'],
                            'counting_detail': item['detail'],
                            'data': item['data'],
                            'result': result
                        })
                        created_details.append(item['detail'])
                    except Exception as e:
                        logger.error(f"Erreur lors de la mise à jour du CountingDetail {item['index']}: {str(e)}")
                        raise e
                
                # Créer les nouveaux en bulk
                if items_to_create:
                    bulk_created_details = self._bulk_create_counting_details(items_to_create, related_objects_cache)
                    
                    # Créer tous les NumeroSerie en bulk pour tous les CountingDetail
                    all_numeros_serie_map = self._bulk_create_all_numeros_serie(items_to_create, bulk_created_details)
                    
                    for i, counting_detail in enumerate(bulk_created_details):
                        item = items_to_create[i]
                        result = {
                            'action': 'created',
                            'counting_detail': {
                                'id': counting_detail.id,
                                'reference': counting_detail.reference,
                                'quantity_inventoried': counting_detail.quantity_inventoried
                            }
                        }
                        
                        # Ajouter les NumeroSerie créés
                        numeros_serie = all_numeros_serie_map.get(counting_detail.id, [])
                        if numeros_serie:
                            result['numeros_serie'] = [
                                {'id': ns.id, 'n_serie': ns.n_serie, 'reference': ns.reference}
                                for ns in numeros_serie
                            ]
                        
                        counting_details_to_process.append({
                            'index': item['index'],
                            'counting_detail': counting_detail,
                            'data': item['data'],
                            'result': result
                        })
                        created_details.append(counting_detail)
                
                # OPTIMISATION 5: Précharger les EcartComptage et dernières séquences
                ecart_cache = self._prefetch_ecarts_and_sequences(created_details)
                
                # OPTIMISATION 6: Traiter tous les comptages en lot (avec cache)
                ecarts_to_update = set()
                
                for item in counting_details_to_process:
                    try:
                        counting_detail = item['counting_detail']
                        i = item['index']
                        
                        # Traiter automatiquement l'écart de comptage (avec cache optimisé)
                        sequence_result = self.traiter_comptage_automatique_optimized(
                            counting_detail,
                            ecart_cache
                        )
                        
                        # Sauvegarder la séquence (ReferenceMixin nécessite save() pour générer référence)
                        sequence_result['sequence'].save()
                        ecarts_to_update.add(sequence_result['ecart'])
                        
                        result = item['result']
                        result['comptage_sequence'] = {
                            'id': sequence_result['sequence'].id,
                            'reference': sequence_result['sequence'].reference,
                            'sequence_number': sequence_result['sequence'].sequence_number,
                            'quantity': sequence_result['sequence'].quantity,
                            'ecart_with_previous': sequence_result['sequence'].ecart_with_previous,
                            'needs_resolution': sequence_result['needs_resolution'],
                            'ecart_value': sequence_result['ecart_value']
                        }
                        result['ecart_comptage'] = {
                            'id': sequence_result['ecart'].id,
                            'reference': sequence_result['ecart'].reference,
                            'resolved': sequence_result['ecart'].resolved,
                            'final_result': sequence_result['ecart'].final_result
                        }
                        if sequence_result.get('final_result') is not None:
                            result['ecart_comptage']['final_result'] = sequence_result['final_result']
                        
                        results.append({
                            'index': i,
                            'data': item['data'],
                            'result': result
                        })
                        
                    except EcartComptageResoluError as e:
                        logger.error(f"Écart résolu pour l'enregistrement {i}: {str(e)}")
                        errors.append({
                            'index': i,
                            'data': item['data'],
                            'error': str(e),
                            'error_type': 'ecart_resolu_error'
                        })
                        raise e
                        
                    except Exception as e:
                        logger.error(f"Erreur lors du traitement de l'enregistrement {i}: {str(e)}")
                        errors.append({
                            'index': i,
                            'data': item['data'],
                            'error': str(e)
                        })
                        raise e
                
                # OPTIMISATION 7: Bulk update des écarts
                if ecarts_to_update:
                    EcartComptage.objects.bulk_update(
                        ecarts_to_update,
                        fields=['total_sequences', 'stopped_sequence', 'final_result']
                    )
            
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
    
    def _get_detail_key(self, data: Dict[str, Any]) -> tuple:
        """
        Génère une clé unique pour identifier un CountingDetail.
        Utilisé pour le cache des détails existants.
        """
        return (
            data.get('counting_id'),
            data.get('location_id'),
            data.get('product_id')
        )
    
    def _prefetch_existing_counting_details(self, data_list: List[Dict[str, Any]]) -> Dict[tuple, CountingDetail]:
        """
        Précharge tous les CountingDetail existants en une seule requête.
        
        Returns:
            Dict avec clé (counting_id, location_id, product_id) et valeur CountingDetail
        """
        if not data_list:
            return {}
        
        # Extraire tous les critères de recherche
        filters = []
        for data in data_list:
            counting_id = data.get('counting_id')
            location_id = data.get('location_id')
            product_id = data.get('product_id')
            
            if counting_id and location_id and product_id:
                filters.append({
                    'counting_id': counting_id,
                    'location_id': location_id,
                    'product_id': product_id
                })
        
        if not filters:
            return {}
        
        # Construire une requête Q pour tous les filtres
        from django.db.models import Q
        q_objects = Q()
        for f in filters:
            q_objects |= Q(**f)
        
        # Récupérer tous les détails en une seule requête
        existing_details = CountingDetail.objects.filter(q_objects).select_related(
            'product', 'location', 'counting__inventory'
        )
        
        # Créer un dictionnaire de mapping
        details_map = {}
        for detail in existing_details:
            key = (detail.counting_id, detail.location_id, detail.product_id if detail.product else None)
            details_map[key] = detail
        
        return details_map
    
    def _prefetch_ecarts_and_sequences(self, counting_details: List[CountingDetail]) -> Dict[tuple, Dict[str, Any]]:
        """
        Précharge tous les EcartComptage et leurs dernières séquences en une seule requête.
        
        Returns:
            Dict avec clé (product_id, location_id, inventory_id) et valeur {
                'ecart': EcartComptage,
                'last_sequence': ComptageSequence ou None
            }
        """
        if not counting_details:
            return {}
        
        # Extraire toutes les combinaisons uniques
        combinations = set()
        for cd in counting_details:
            if cd.product and cd.location and cd.counting.inventory:
                combinations.add((
                    cd.product_id,
                    cd.location_id,
                    cd.counting.inventory_id
                ))
        
        if not combinations:
            return {}
        
        product_ids = [c[0] for c in combinations]
        location_ids = [c[1] for c in combinations]
        inventory_ids = [c[2] for c in combinations]
        
        # Récupérer les séquences correspondantes en une seule requête optimisée
        sequences_query = ComptageSequence.objects.filter(
            counting_detail__product_id__in=product_ids,
            counting_detail__location_id__in=location_ids,
            counting_detail__counting__inventory_id__in=inventory_ids
        ).select_related(
            'ecart_comptage', 
            'counting_detail__product', 
            'counting_detail__location',
            'counting_detail__counting__inventory'
        ).order_by(
            'counting_detail__product_id',
            'counting_detail__location_id', 
            'counting_detail__counting__inventory_id',
            'sequence_number'
        )
        
        # Grouper par combinaison et conserver toutes les séquences (en ordre croissant)
        cache = {}
        for seq in sequences_query:
            key = (
                seq.counting_detail.product_id, 
                seq.counting_detail.location_id, 
                seq.counting_detail.counting.inventory_id
            )
            
            if key not in cache:
                cache[key] = {
                    'ecart': seq.ecart_comptage,
                    'last_sequence': seq,
                    'last_sequence_number': seq.sequence_number,
                    'sequences': [seq]
                }
            else:
                cache[key]['sequences'].append(seq)
                cache[key]['last_sequence'] = seq
                cache[key]['last_sequence_number'] = seq.sequence_number
        
        # Charger les écarts résolus pour vérification en une seule requête
        ecart_ids = list({item['ecart'].id for item in cache.values() if item.get('ecart')})
        if ecart_ids:
            resolved_ecarts = set(
                EcartComptage.objects.filter(id__in=ecart_ids, resolved=True)
                .values_list('id', flat=True)
            )
            for key, item in cache.items():
                if item['ecart'].id in resolved_ecarts:
                    item['ecart'].resolved = True
        
        # Initialiser les entrées sans séquences pour les combinaisons sans historique
        for combination in combinations:
            if combination not in cache:
                cache[combination] = {
                    'ecart': None,
                    'last_sequence': None,
                    'last_sequence_number': 0,
                    'sequences': []
                }
        
        return cache
    
    def traiter_comptage_automatique_optimized(
        self, 
        counting_detail: CountingDetail,
        ecart_cache: Dict[tuple, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Version optimisée de traiter_comptage_automatique qui utilise un cache préchargé.
        
        Args:
            counting_detail: Instance de CountingDetail
            ecart_cache: Cache des écarts préchargés
            
        Returns:
            dict: {
                'ecart': EcartComptage instance,
                'sequence': ComptageSequence instance (non sauvegardée),
                'ecart_value': int ou None,
                'needs_resolution': bool
            }
        """
        product = counting_detail.product
        location = counting_detail.location
        inventory = counting_detail.counting.inventory
        
        if not product or not location:
            raise ValidationError("Product et Location sont obligatoires pour créer un EcartComptage")
        
        key = (product.id, location.id, inventory.id)
        cache_entry = ecart_cache.get(key)
        entry_has_ecart = cache_entry and cache_entry.get('ecart')
        
        if entry_has_ecart:
            ecart = cache_entry['ecart']
            # Vérifier si résolu
            if ecart.resolved:
                raise EcartComptageResoluError(ecart, product, location)
            
            last_sequence = cache_entry.get('last_sequence')
            last_sequence_number = cache_entry.get('last_sequence_number', 0)
        else:
            # Créer un nouvel écart
            ecart = EcartComptage(
                inventory=inventory,
                total_sequences=0,
                resolved=False,
                stopped_reason=None,
                final_result=None,
                justification=None
            )
            ecart.reference = ecart.generate_reference(EcartComptage.REFERENCE_PREFIX)
            ecart.save()
            last_sequence = None
            last_sequence_number = 0
            # Mettre à jour le cache
            if not cache_entry:
                ecart_cache[key] = {
                    'ecart': ecart,
                    'last_sequence': None,
                    'last_sequence_number': 0,
                    'sequences': []
                }
            else:
                cache_entry['ecart'] = ecart
                cache_entry['last_sequence'] = None
                cache_entry['last_sequence_number'] = 0
                cache_entry.setdefault('sequences', [])
        
        cache_entry = ecart_cache.get(key)
        cache_entry.setdefault('sequences', [])
        
        # Calculer le nouveau numéro de séquence
        nouveau_numero = last_sequence_number + 1
        
        # Calculer l'écart avec le précédent
        ecart_value = None
        if last_sequence:
            ecart_value = counting_detail.quantity_inventoried - last_sequence.quantity
        
        # Créer la nouvelle séquence (sera sauvegardée après)
        nouvelle_sequence = ComptageSequence(
            ecart_comptage=ecart,
            sequence_number=nouveau_numero,
            counting_detail=counting_detail,
            quantity=counting_detail.quantity_inventoried,
            ecart_with_previous=ecart_value
        )
        
        # Mettre à jour l'écart
        ecart.total_sequences = nouveau_numero
        ecart.stopped_sequence = nouveau_numero
        
        # Mettre à jour le cache
        cache_entry['last_sequence'] = nouvelle_sequence
        cache_entry['last_sequence_number'] = nouveau_numero
        cache_entry['sequences'].append(nouvelle_sequence)
        
        # Mettre à jour le résultat final éventuel (seulement si 2 comptages ou plus)
        final_result = None
        if len(cache_entry['sequences']) >= 2:
            final_result = self._calculate_consensus_result(cache_entry['sequences'], ecart.final_result)
            if final_result is not None:
                ecart.final_result = final_result
        
        return {
            "ecart": ecart,
            "sequence": nouvelle_sequence,
            "ecart_value": ecart_value,
            "needs_resolution": ecart_value == 0,
            "final_result": final_result
        }
    
    def _prefetch_all_related_objects(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Précharge tous les objets liés nécessaires en une seule fois.
        Évite les N requêtes lors de _get_related_objects.
        
        Returns:
            Dict avec clés : 'countings', 'locations', 'products', 'assignments', 'job_details'
        """
        # Extraire tous les IDs uniques
        counting_ids = set()
        location_ids = set()
        product_ids = set()
        assignment_ids = set()
        
        for data in data_list:
            if data.get('counting_id'):
                counting_ids.add(data['counting_id'])
            if data.get('location_id'):
                location_ids.add(data['location_id'])
            if data.get('product_id'):
                product_ids.add(data['product_id'])
            if data.get('assignment_id'):
                assignment_ids.add(data['assignment_id'])
        
        # Charger tous les objets en une seule requête chacun
        cache = {}
        
        if counting_ids:
            cache['countings'] = {
                c.id: c for c in Counting.objects.filter(id__in=counting_ids)
            }
        else:
            cache['countings'] = {}
        
        if location_ids:
            cache['locations'] = {
                l.id: l for l in Location.objects.filter(id__in=location_ids)
            }
        else:
            cache['locations'] = {}
        
        if product_ids:
            cache['products'] = {
                p.id: p for p in Product.objects.filter(id__in=product_ids)
            }
        else:
            cache['products'] = {}
        
        if assignment_ids:
            assignments = Assigment.objects.filter(id__in=assignment_ids).select_related('job')
            cache['assignments'] = {a.id: a for a in assignments}
            # Extraire les job_ids pour charger les JobDetail
            job_ids = [a.job.id for a in assignments if a.job]
        else:
            cache['assignments'] = {}
            job_ids = []
        
        # Charger les JobDetail pour toutes les combinaisons
        cache['job_details'] = {}
        if job_ids and counting_ids and location_ids:
            job_details = JobDetail.objects.filter(
                job_id__in=job_ids,
                counting_id__in=counting_ids,
                location_id__in=location_ids
            ).select_related('job', 'counting', 'location')
            
            for jd in job_details:
                key = (jd.job_id, jd.counting_id, jd.location_id)
                cache['job_details'][key] = jd
        
        return cache
    
    def _validate_all_data_batch(self, data_list: List[Dict[str, Any]], related_cache: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Valide tous les éléments en lot en utilisant le cache préchargé.
        
        Returns:
            List[Dict] avec 'valid', 'error', 'related_objects' pour chaque élément
        """
        results = []
        
        for data in data_list:
            result = {'valid': True, 'error': None, 'related_objects': {}}
            
            try:
                # Récupérer les objets depuis le cache
                counting_id = data.get('counting_id')
                location_id = data.get('location_id')
                product_id = data.get('product_id')
                assignment_id = data.get('assignment_id')
                
                # Validation Counting
                if not counting_id:
                    result['valid'] = False
                    result['error'] = "Le champ 'counting_id' est obligatoire"
                    results.append(result)
                    continue
                
                counting = related_cache['countings'].get(counting_id)
                if not counting:
                    result['valid'] = False
                    result['error'] = f"Comptage avec l'ID {counting_id} non trouvé"
                    results.append(result)
                    continue
                
                # Validation Location
                if not location_id:
                    result['valid'] = False
                    result['error'] = "Le champ 'location_id' est obligatoire"
                    results.append(result)
                    continue
                
                location = related_cache['locations'].get(location_id)
                if not location:
                    result['valid'] = False
                    result['error'] = f"Emplacement avec l'ID {location_id} non trouvé"
                    results.append(result)
                    continue
                
                # Validation Product (optionnel selon mode)
                product = None
                if product_id:
                    product = related_cache['products'].get(product_id)
                    if not product:
                        result['valid'] = False
                        result['error'] = f"Produit avec l'ID {product_id} non trouvé"
                        results.append(result)
                        continue
                    
                    # Validation selon mode de comptage
                    if counting.count_mode == "par article" and not product_id:
                        result['valid'] = False
                        result['error'] = "Le produit est obligatoire pour le mode 'par article'"
                        results.append(result)
                        continue
                
                # Validation Assignment
                if not assignment_id:
                    result['valid'] = False
                    result['error'] = "Le champ 'assignment_id' est obligatoire"
                    results.append(result)
                    continue
                
                assignment = related_cache['assignments'].get(assignment_id)
                if not assignment:
                    result['valid'] = False
                    result['error'] = f"Assignment avec l'ID {assignment_id} non trouvé"
                    results.append(result)
                    continue
                
                # Validation JobDetail
                job_detail_key = (assignment.job_id, counting_id, location_id)
                job_detail = related_cache['job_details'].get(job_detail_key)
                if not job_detail:
                    result['valid'] = False
                    result['error'] = f"JobDetail non trouvé pour job {assignment.job_id}, counting {counting_id}, location {location_id}"
                    results.append(result)
                    continue
                
                # Validation quantité
                quantity = data.get('quantity_inventoried')
                if not quantity or quantity <= 0:
                    result['valid'] = False
                    result['error'] = "La quantité inventoriée doit être positive"
                    results.append(result)
                    continue
                
                # Validation propriétés produit (simplifiée, sans requête masterdata.NSerie pour performance)
                if product and counting.count_mode == "par article":
                    if counting.dlc and product.dlc and not data.get('dlc'):
                        result['valid'] = False
                        result['error'] = "Le champ 'dlc' est obligatoire"
                        results.append(result)
                        continue
                    
                    if counting.n_lot and product.n_lot and not data.get('n_lot'):
                        result['valid'] = False
                        result['error'] = "Le champ 'n_lot' est obligatoire"
                        results.append(result)
                        continue
                
                # Tout est valide
                result['related_objects'] = {
                    'counting': counting,
                    'location': location,
                    'product': product,
                    'assignment': assignment,
                    'job_detail': job_detail,
                    'job': assignment.job
                }
                
            except Exception as e:
                result['valid'] = False
                result['error'] = str(e)
            
            results.append(result)
        
        return results
    
    def _bulk_create_counting_details(
        self, 
        items_to_create: List[Dict[str, Any]], 
        related_cache: Dict[str, Any]
    ) -> List[CountingDetail]:
        """
        Crée tous les CountingDetail en bulk.
        
        Args:
            items_to_create: Liste des éléments à créer avec leurs objets liés
            related_cache: Cache des objets liés
            
        Returns:
            List[CountingDetail]: Liste des CountingDetail créés (avec IDs)
        """
        counting_details_to_create = []
        
        for item in items_to_create:
            data = item['data']
            related = item['related']
            
            counting_detail = CountingDetail(
                quantity_inventoried=data['quantity_inventoried'],
                product=related['product'],
                dlc=data.get('dlc'),
                n_lot=data.get('n_lot'),
                location=related['location'],
                counting=related['counting'],
                job=related['job'],
                last_synced_at=timezone.now()
            )
            
            # Générer la référence temporaire (sera regénérée après save)
            counting_detail.reference = counting_detail.generate_reference(CountingDetail.REFERENCE_PREFIX)
            
            counting_details_to_create.append(counting_detail)
        
        # Bulk create (ne génère pas automatiquement les références)
        CountingDetail.objects.bulk_create(counting_details_to_create)
        
        # Régénérer les références avec les IDs réels
        for cd in counting_details_to_create:
            if cd.id:
                cd.reference = cd.generate_reference(CountingDetail.REFERENCE_PREFIX)
        
        # Bulk update des références
        CountingDetail.objects.bulk_update(counting_details_to_create, fields=['reference'])
        
        # Recharger les objets avec les relations pour accès ultérieur à counting.inventory
        # Nécessaire car bulk_create ne charge pas automatiquement les relations
        counting_detail_ids = [cd.id for cd in counting_details_to_create if cd.id]
        if counting_detail_ids:
            # Recharger avec select_related pour avoir counting.inventory accessible
            reloaded_details = {
                cd.id: cd for cd in CountingDetail.objects.filter(id__in=counting_detail_ids)
                .select_related('product', 'location', 'counting__inventory', 'counting', 'job')
            }
            # Remplacer les objets dans la liste
            for i, cd in enumerate(counting_details_to_create):
                if cd.id and cd.id in reloaded_details:
                    counting_details_to_create[i] = reloaded_details[cd.id]
        
        # Mettre à jour les JobDetail en bulk aussi
        job_details_to_update = []
        job_detail_keys_processed = set()
        
        for item in items_to_create:
            related = item['related']
            job_detail = related['job_detail']
            
            if job_detail.id not in job_detail_keys_processed:
                job_detail.status = 'TERMINE'
                job_detail.termine_date = timezone.now()
                job_details_to_update.append(job_detail)
                job_detail_keys_processed.add(job_detail.id)
        
        if job_details_to_update:
            JobDetail.objects.bulk_update(job_details_to_update, fields=['status', 'termine_date'])
        
        return counting_details_to_create
    
    def _bulk_create_all_numeros_serie(
        self, 
        items_to_create: List[Dict[str, Any]], 
        bulk_created_details: List[CountingDetail]
    ) -> Dict[int, List[NSerieInventory]]:
        """
        Crée tous les NumeroSerie en bulk pour tous les CountingDetail.
        
        Args:
            items_to_create: Liste des éléments avec leurs données
            bulk_created_details: Liste des CountingDetail créés (dans le même ordre)
            
        Returns:
            Dict[int, List[NSerieInventory]]: Mapping counting_detail_id -> liste de NumeroSerie
        """
        all_numeros_serie_to_create = []
        detail_id_to_nserie = {}
        
        # Grouper tous les NumeroSerie à créer
        for i, counting_detail in enumerate(bulk_created_details):
            item = items_to_create[i]
            numeros_serie_data = item['data'].get('numeros_serie', [])
            
            if numeros_serie_data:
                numeros_serie_list = []
                for ns_data in numeros_serie_data:
                    nserie = NSerieInventory(
                        n_serie=ns_data['n_serie'],
                        counting_detail=counting_detail
                    )
                    # Générer référence temporaire
                    nserie.reference = nserie.generate_reference(NSerieInventory.REFERENCE_PREFIX)
                    all_numeros_serie_to_create.append(nserie)
                    numeros_serie_list.append(nserie)
                
                detail_id_to_nserie[counting_detail.id] = numeros_serie_list
        
        if all_numeros_serie_to_create:
            # Bulk create de tous les NumeroSerie en une seule fois
            NSerieInventory.objects.bulk_create(all_numeros_serie_to_create)
            
            # Régénérer les références avec les IDs réels
            for ns in all_numeros_serie_to_create:
                if ns.id:
                    ns.reference = ns.generate_reference(NSerieInventory.REFERENCE_PREFIX)
            
            # Bulk update des références
            NSerieInventory.objects.bulk_update(all_numeros_serie_to_create, fields=['reference'])
        
        return detail_id_to_nserie
    
    def validate_counting_details_batch(self, data_list: List[Dict[str, Any]], job_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Valide plusieurs CountingDetail sans les créer.
        
        Args:
            data_list: Liste des données de comptage détaillé
            job_id: ID du job (optionnel, pour filtrer par job)
            
        Returns:
            Dict[str, Any]: Résultat de la validation
        """
        try:
            logger.info(f"Validation en lot de {len(data_list)} CountingDetail")
            
            results = []
            errors = []
            
            for i, data in enumerate(data_list):
                validation_result = self._validate_single_counting_detail(i, data, job_id=job_id)
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
    
    def _validate_single_counting_detail(self, index: int, data: Dict[str, Any], job_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Valide un seul CountingDetail.
        
        Args:
            index: Index de l'élément dans la liste
            data: Données du comptage détaillé
            job_id: ID du job (optionnel)
            
        Returns:
            Dict[str, Any]: Résultat de la validation
        """
        try:
            # La validation complète sera faite par le use case lors de la création
            existing_detail = self._find_existing_counting_detail(data, job_id=job_id)
            
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
    
    def _find_existing_counting_detail(self, data: Dict[str, Any], job_id: Optional[int] = None) -> Optional[CountingDetail]:
        """
        Recherche un CountingDetail existant basé sur les critères de matching.
        
        Args:
            data: Données du comptage détaillé
            job_id: ID du job (optionnel, pour filtrer par job)
            
        Returns:
            Optional[CountingDetail]: Le CountingDetail existant ou None
        """
        try:
            queryset = CountingDetail.objects.filter(
                counting_id=data['counting_id'],
                location_id=data['location_id']
            )
            
            # Filtrer par product_id si fourni (peut être None pour certains modes de comptage)
            if data.get('product_id'):
                queryset = queryset.filter(product_id=data['product_id'])
            else:
                queryset = queryset.filter(product__isnull=True)
            
            # Filtrer par job_id si fourni
            if job_id:
                queryset = queryset.filter(job_id=job_id)
            
            return queryset.first()
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
            
            # Mettre à jour les NumeroSerie si fournis (optimisé en bulk)
            numeros_serie = []
            if 'numeros_serie' in data and data['numeros_serie']:
                # Supprimer les anciens NumeroSerie
                NSerieInventory.objects.filter(counting_detail=counting_detail).delete()
                
                # Créer les nouveaux NumeroSerie en bulk
                numeros_serie_to_create = []
                for n_serie_data in data['numeros_serie']:
                    n_serie = NSerieInventory(
                        n_serie=n_serie_data['n_serie'],
                        counting_detail=counting_detail
                    )
                    n_serie.reference = n_serie.generate_reference(NSerieInventory.REFERENCE_PREFIX)
                    numeros_serie_to_create.append(n_serie)
                
                if numeros_serie_to_create:
                    NSerieInventory.objects.bulk_create(numeros_serie_to_create)
                    # Régénérer les références
                    for ns in numeros_serie_to_create:
                        if ns.id:
                            ns.reference = ns.generate_reference(NSerieInventory.REFERENCE_PREFIX)
                    NSerieInventory.objects.bulk_update(numeros_serie_to_create, fields=['reference'])
                    
                    numeros_serie = [
                        {
                            'id': ns.id,
                            'n_serie': ns.n_serie,
                            'reference': ns.reference
                        }
                        for ns in numeros_serie_to_create
                    ]
            
            return {
                'counting_detail': {
                    'id': counting_detail.id,
                    'reference': counting_detail.reference,
                    'quantity_inventoried': counting_detail.quantity_inventoried,
                    'product_id': counting_detail.product.id if counting_detail.product else None,
                    'location_id': counting_detail.location.id,
                    'counting_id': counting_detail.counting.id,
                    'job_id': counting_detail.job.id if counting_detail.job else None,
                    'created_at': counting_detail.created_at,
                    'updated_at': counting_detail.updated_at
                },
                'numeros_serie': numeros_serie
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du CountingDetail: {str(e)}")
            raise e
    
    def get_counting_details_by_counting(self, counting_id: int, job_id: Optional[int] = None):
        """
        Récupère tous les CountingDetail d'un comptage.
        
        Args:
            counting_id: ID du comptage
            job_id: ID du job (optionnel, pour filtrer par job)
            
        Returns:
            List[CountingDetail]: Liste des CountingDetail
        """
        try:
            from apps.inventory.models import Counting
            counting = Counting.objects.get(id=counting_id)
            queryset = CountingDetail.objects.filter(counting=counting)
            if job_id:
                queryset = queryset.filter(job_id=job_id)
            return queryset.order_by('-created_at')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des CountingDetail: {str(e)}")
            return []
    
    def get_counting_details_by_location(self, location_id: int, job_id: Optional[int] = None):
        """
        Récupère tous les CountingDetail d'un emplacement.
        
        Args:
            location_id: ID de l'emplacement
            job_id: ID du job (optionnel, pour filtrer par job)
            
        Returns:
            List[CountingDetail]: Liste des CountingDetail
        """
        try:
            queryset = CountingDetail.objects.filter(location_id=location_id)
            if job_id:
                queryset = queryset.filter(job_id=job_id)
            return queryset.order_by('-created_at')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des CountingDetail par emplacement: {str(e)}")
            return []
    
    def get_counting_details_by_product(self, product_id: int, job_id: Optional[int] = None):
        """
        Récupère tous les CountingDetail d'un produit.
        
        Args:
            product_id: ID du produit
            job_id: ID du job (optionnel, pour filtrer par job)
            
        Returns:
            List[CountingDetail]: Liste des CountingDetail
        """
        try:
            queryset = CountingDetail.objects.filter(product_id=product_id)
            if job_id:
                queryset = queryset.filter(job_id=job_id)
            return queryset.order_by('-created_at')
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
    
    def detecter_ou_creer_ecart_comptage(self, counting_detail: CountingDetail) -> EcartComptage:
        """
        Détecte automatiquement ou crée un EcartComptage pour un CountingDetail.
        
        Critère de regroupement : même produit + même location + même inventaire.
        
        Args:
            counting_detail: Instance de CountingDetail
        
        Returns:
            EcartComptage: L'écart existant ou nouvellement créé
        
        Raises:
            EcartComptageResoluError: Si l'écart existant est déjà résolu
        """
        product = counting_detail.product
        location = counting_detail.location
        inventory = counting_detail.counting.inventory
        
        # Chercher un EcartComptage existant pour cette combinaison
        # On vérifie via les ComptageSequence liées
        ecart_existant = None
        
        # Recherche dans les séquences existantes ayant le même produit, location et inventory
        sequences_existantes = ComptageSequence.objects.filter(
            counting_detail__product=product,
            counting_detail__location=location,
            counting_detail__counting__inventory=inventory
        ).select_related('ecart_comptage', 'counting_detail__product', 'counting_detail__location')
        
        if sequences_existantes.exists():
            # Récupérer l'écart existant (toutes les séquences d'un même écart)
            ecart_existant = sequences_existantes.first().ecart_comptage
            
            # Vérifier que cet écart n'est pas déjà résolu
            if ecart_existant.resolved:
                # Lever une exception : les comptages sont terminés
                raise EcartComptageResoluError(
                    ecart_existant, 
                    product, 
                    location
                )
        
        # Si aucun écart existant ou si résolu → créer un nouvel écart
        if not ecart_existant:
            ecart_existant = EcartComptage(
                inventory=inventory,
                total_sequences=0,
                resolved=False,
                stopped_reason=None,
                final_result=None,
                justification=None
            )
            ecart_existant.reference = ecart_existant.generate_reference(EcartComptage.REFERENCE_PREFIX)
            ecart_existant.save()
        
        return ecart_existant
    
    def traiter_comptage_automatique(self, counting_detail: CountingDetail) -> Dict[str, Any]:
        """
        Traite automatiquement un nouveau CountingDetail :
        - Crée ou récupère l'EcartComptage (lève exception si résolu)
        - Ajoute la ComptageSequence
        - Calcule l'écart avec le précédent
        - NE RÉSOUT PAS automatiquement (même si écart = 0)
        
        Args:
            counting_detail: Instance de CountingDetail
        
        Returns:
            dict: {
                'ecart': EcartComptage instance,
                'sequence': ComptageSequence instance,
                'ecart_value': int ou None (différence avec précédent),
                'needs_resolution': bool (True si écart = 0, pour info seulement)
            }
        
        Raises:
            EcartComptageResoluError: Si on essaie d'ajouter à un écart résolu
        """
        # 1. Détecter ou créer l'écart (lève une exception si résolu)
        ecart = self.detecter_ou_creer_ecart_comptage(counting_detail)
        
        # 2. Récupérer la dernière séquence si elle existe
        derniere_sequence = ecart.counting_sequences.order_by('-sequence_number').first()
        
        # 3. Calculer le numéro de la nouvelle séquence
        nouveau_numero = (derniere_sequence.sequence_number + 1) if derniere_sequence else 1
        
        # 4. Calculer l'écart avec le précédent
        ecart_value = None
        if derniere_sequence:
            # Toujours stocker l'écart en valeur absolue pour éviter les valeurs négatives
            ecart_value = abs(counting_detail.quantity_inventoried - derniere_sequence.quantity)
        
        # 5. Créer la nouvelle séquence
        nouvelle_sequence = ComptageSequence(
            ecart_comptage=ecart,
            sequence_number=nouveau_numero,
            counting_detail=counting_detail,
            quantity=counting_detail.quantity_inventoried,
            ecart_with_previous=ecart_value
        )
        # Générer la référence avant sauvegarde pour éviter les doublons
        nouvelle_sequence.reference = nouvelle_sequence.generate_reference(ComptageSequence.REFERENCE_PREFIX)
        
        # Mettre à jour l'écart
        ecart.total_sequences = nouveau_numero
        ecart.stopped_sequence = nouveau_numero
        ecart.save()
        
        # 7. Ne pas résoudre automatiquement même si écart = 0
        # La résolution se fera manuellement via resoudre_ecart_manuellement()
        
        return {
            "ecart": ecart,
            "sequence": nouvelle_sequence,
            "ecart_value": ecart_value,
            "needs_resolution": ecart_value == 0  # Info seulement, pas de résolution auto
        }

    def _calculate_consensus_result(
        self,
        sequences: List[ComptageSequence],
        current_result: Optional[int]
    ) -> Optional[int]:
        """
        Détermine le résultat final d'un écart selon les règles métier :
        - Nécessite au moins 2 comptages pour calculer un résultat.
        - Deux comptages identiques suffisent à confirmer une valeur.
        - Si plusieurs valeurs sont confirmées, on privilégie la plus récente.
        - Si aucun consensus, on conserve le résultat courant.
        """
        if len(sequences) < 2:
            return None  # Pas de résultat si moins de 2 comptages
        
        counts: Dict[int, int] = {}
        latest_index: Dict[int, int] = {}
        for index, sequence in enumerate(sequences):
            quantity = sequence.quantity
            counts[quantity] = counts.get(quantity, 0) + 1
            latest_index[quantity] = index
        
        # Filtrer les valeurs présentes au moins deux fois
        consensus_candidates = [
            (counts[value], latest_index[value], value)
            for value in counts
            if counts[value] >= 2
        ]
        
        if not consensus_candidates:
            return current_result
        
        # Si le résultat courant est encore valide, on le conserve
        if current_result is not None and counts.get(current_result, 0) >= 2:
            return current_result
        
        # Choisir la valeur avec le plus grand nombre d'occurrences, puis la plus récente
        consensus_candidates.sort(key=lambda item: (item[0], item[1]))
        return consensus_candidates[-1][2]
