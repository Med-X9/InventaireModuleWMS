"""
Use case pour le traitement automatique des écarts de comptage.

Ce use case respecte les principes SOLID, KISS et DRY :
- Single Responsibility : Traite uniquement les écarts automatiquement
- Open/Closed : Extensible sans modification
- Dependency Inversion : Dépend des abstractions (modèles Django)
- KISS : Logique simple et claire
- DRY : Réutilise la logique de calcul de consensus
"""

from typing import Dict, Any, List, Optional
from django.core.exceptions import ValidationError

from apps.inventory.models import CountingDetail, EcartComptage, ComptageSequence
from apps.mobile.exceptions import EcartComptageResoluError
import logging

logger = logging.getLogger(__name__)


class EcartComptageAutomaticProcessingUseCase:
    """
    Use case pour traiter automatiquement les écarts de comptage.
    
    Responsabilité unique : Créer/mettre à jour les ComptageSequence et EcartComptage
    de manière automatique lors de la création d'un CountingDetail.
    
    Exemple d'utilisation :
        use_case = EcartComptageAutomaticProcessingUseCase()
        result = use_case.execute(counting_detail, ecart_cache)
        
        if result['needs_resolution']:
            print(f"Écart détecté : {result['ecart_value']}")
    """
    
    def __init__(self):
        """Initialise le use case."""
        pass
    
    def execute(
        self, 
        counting_detail: CountingDetail,
        ecart_cache: Dict[tuple, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Traite automatiquement l'écart de comptage pour un CountingDetail.
        
        Args:
            counting_detail: Instance de CountingDetail à traiter
            ecart_cache: Cache des écarts préchargés avec la structure :
                {
                    (product_id, location_id, inventory_id): {
                        'ecart': EcartComptage,
                        'last_sequence': ComptageSequence ou None,
                        'last_sequence_number': int,
                        'sequences': List[ComptageSequence],
                        'counting_detail_sequences': Dict[counting_detail_id, ComptageSequence]
                    }
                }
        
        Returns:
            Dict avec :
                - 'ecart': EcartComptage instance
                - 'sequence': ComptageSequence instance (non sauvegardée)
                - 'ecart_value': int ou None - Écart avec la séquence précédente
                - 'needs_resolution': bool - True si écart = 0 (peut être résolu automatiquement)
                - 'final_result': int ou None - Résultat final calculé si consensus
                - 'is_update': bool - True si mise à jour, False si création
        
        Raises:
            ValidationError: Si product ou location manquants
            EcartComptageResoluError: Si l'écart est déjà résolu
        """
        # Validation des prérequis
        self._validate_prerequisites(counting_detail)
        
        # Récupérer ou créer l'EcartComptage
        ecart, cache_entry = self._get_or_create_ecart(counting_detail, ecart_cache)
        
        # Vérifier si l'écart est résolu
        if ecart.resolved:
            raise EcartComptageResoluError(ecart, counting_detail.product, counting_detail.location)
        
        # Traiter la séquence (création ou mise à jour)
        sequence_result = self._process_sequence(counting_detail, ecart, cache_entry)
        
        # Calculer le consensus si possible
        final_result = self._calculate_consensus(cache_entry['sequences'], ecart.final_result)
        if final_result is not None:
            ecart.final_result = final_result
        
        return {
            "ecart": ecart,
            "sequence": sequence_result['sequence'],
            "ecart_value": sequence_result['ecart_value'],
            "needs_resolution": sequence_result['ecart_value'] == 0 if sequence_result['ecart_value'] is not None else False,
            "final_result": final_result,
            "is_update": sequence_result['is_update']
        }
    
    def _validate_prerequisites(self, counting_detail: CountingDetail) -> None:
        """
        Valide les prérequis pour le traitement automatique.
        
        Args:
            counting_detail: Le CountingDetail à valider
        
        Raises:
            ValidationError: Si product ou location manquants
        """
        if not counting_detail.product or not counting_detail.location:
            raise ValidationError("Product et Location sont obligatoires pour créer un EcartComptage")
    
    def _get_or_create_ecart(
        self, 
        counting_detail: CountingDetail, 
        ecart_cache: Dict[tuple, Dict[str, Any]]
    ) -> tuple:
        """
        Récupère ou crée l'EcartComptage.
        
        Args:
            counting_detail: Le CountingDetail
            ecart_cache: Cache des écarts
        
        Returns:
            tuple: (ecart, cache_entry)
        """
        key = (
            counting_detail.product.id, 
            counting_detail.location.id, 
            counting_detail.counting.inventory.id
        )
        
        cache_entry = ecart_cache.get(key)
        entry_has_ecart = cache_entry and cache_entry.get('ecart')
        
        if entry_has_ecart:
            ecart = cache_entry['ecart']
            # Initialiser les structures si manquantes
            cache_entry.setdefault('sequences', [])
            cache_entry.setdefault('counting_detail_sequences', {})
        else:
            # Créer un nouvel écart
            ecart = EcartComptage(
                inventory=counting_detail.counting.inventory,
                total_sequences=0,
                resolved=False,
                stopped_reason=None,
                final_result=None,
                justification=None
            )
            ecart.reference = ecart.generate_reference(EcartComptage.REFERENCE_PREFIX)
            ecart.save()
            
            # Initialiser le cache
            if not cache_entry:
                ecart_cache[key] = {
                    'ecart': ecart,
                    'last_sequence': None,
                    'last_sequence_number': 0,
                    'sequences': [],
                    'counting_detail_sequences': {}
                }
            else:
                cache_entry['ecart'] = ecart
                cache_entry['last_sequence'] = None
                cache_entry['last_sequence_number'] = 0
                cache_entry.setdefault('sequences', [])
                cache_entry.setdefault('counting_detail_sequences', {})
            
            cache_entry = ecart_cache[key]
        
        return ecart, cache_entry
    
    def _process_sequence(
        self, 
        counting_detail: CountingDetail, 
        ecart: EcartComptage, 
        cache_entry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Traite la séquence (création ou mise à jour).
        
        Args:
            counting_detail: Le CountingDetail
            ecart: L'EcartComptage
            cache_entry: L'entrée du cache
        
        Returns:
            Dict avec 'sequence', 'ecart_value', 'is_update'
        """
        existing_sequence = cache_entry['counting_detail_sequences'].get(counting_detail.id)
        
        if existing_sequence:
            return self._update_existing_sequence(counting_detail, existing_sequence, cache_entry)
        else:
            return self._create_new_sequence(counting_detail, ecart, cache_entry)
    
    def _update_existing_sequence(
        self, 
        counting_detail: CountingDetail, 
        existing_sequence: ComptageSequence, 
        cache_entry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Met à jour une séquence existante.
        
        Args:
            counting_detail: Le CountingDetail
            existing_sequence: La séquence existante
            cache_entry: L'entrée du cache
        
        Returns:
            Dict avec 'sequence', 'ecart_value', 'is_update'
        """
        logger.info(f"Mise à jour de la séquence existante {existing_sequence.id} pour CountingDetail {counting_detail.id}")
        
        # Mettre à jour la quantité
        existing_sequence.quantity = counting_detail.quantity_inventoried
        
        # Recalculer l'écart avec la séquence précédente
        previous_sequence = self._find_previous_sequence(existing_sequence, cache_entry['sequences'])
        ecart_value = None
        
        if previous_sequence:
            ecart_value = abs(counting_detail.quantity_inventoried - previous_sequence.quantity)
            existing_sequence.ecart_with_previous = ecart_value
        else:
            existing_sequence.ecart_with_previous = None
        
        # Mettre à jour dans le cache
        for idx, seq in enumerate(cache_entry['sequences']):
            if seq.id == existing_sequence.id:
                cache_entry['sequences'][idx] = existing_sequence
                break
        
        return {
            'sequence': existing_sequence,
            'ecart_value': ecart_value,
            'is_update': True
        }
    
    def _create_new_sequence(
        self, 
        counting_detail: CountingDetail, 
        ecart: EcartComptage, 
        cache_entry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crée une nouvelle séquence.
        
        Args:
            counting_detail: Le CountingDetail
            ecart: L'EcartComptage
            cache_entry: L'entrée du cache
        
        Returns:
            Dict avec 'sequence', 'ecart_value', 'is_update'
        """
        logger.info(f"Création d'une nouvelle séquence pour CountingDetail {counting_detail.id}")
        
        # Calculer le nouveau numéro de séquence
        nouveau_numero = cache_entry['last_sequence_number'] + 1
        
        # Calculer l'écart avec le précédent
        last_sequence = cache_entry.get('last_sequence')
        ecart_value = None
        if last_sequence:
            ecart_value = abs(counting_detail.quantity_inventoried - last_sequence.quantity)
        
        # Créer la nouvelle séquence
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
        cache_entry['counting_detail_sequences'][counting_detail.id] = nouvelle_sequence
        
        return {
            'sequence': nouvelle_sequence,
            'ecart_value': ecart_value,
            'is_update': False
        }
    
    def _find_previous_sequence(
        self, 
        current_sequence: ComptageSequence, 
        all_sequences: List[ComptageSequence]
    ) -> Optional[ComptageSequence]:
        """
        Trouve la séquence précédente dans la liste.
        
        Args:
            current_sequence: La séquence actuelle
            all_sequences: Liste de toutes les séquences
        
        Returns:
            ComptageSequence précédente ou None
        """
        sequences_before = [s for s in all_sequences if s.id != current_sequence.id]
        if not sequences_before:
            return None
        
        # Trier par sequence_number
        sequences_before.sort(key=lambda x: x.sequence_number)
        
        # Trouver la séquence avec le sequence_number immédiatement inférieur
        current_seq_number = current_sequence.sequence_number
        for seq in reversed(sequences_before):
            if seq.sequence_number < current_seq_number:
                return seq
        
        return None
    
    def _calculate_consensus(
        self, 
        sequences: List[ComptageSequence], 
        current_result: Optional[int]
    ) -> Optional[int]:
        """
        Calcule le résultat final selon les règles de consensus.
        
        Règles :
        1. Si < 2 séquences → pas de consensus
        2. Si dernière séquence = au moins une précédente → consensus trouvé
        3. Si exactement 2 séquences différentes → pas de consensus
        4. Sinon → conserver le résultat actuel s'il existe
        
        Args:
            sequences: Liste de toutes les ComptageSequence (ordre chronologique)
            current_result: Résultat actuel de l'écart
        
        Returns:
            int ou None - Résultat final calculé
        """
        if len(sequences) < 2:
            return None
        
        # Prendre le dernier comptage (le plus récent)
        comptage_actuel = sequences[-1]
        quantite_actuelle = comptage_actuel.quantity
        
        # Extraire toutes les quantités des comptages précédents
        quantites_precedentes = [seq.quantity for seq in sequences[:-1]]
        
        # Vérifier si le comptage actuel correspond à au moins un comptage précédent
        if quantite_actuelle in quantites_precedentes:
            # Consensus trouvé → retourner cette quantité
            return quantite_actuelle
        else:
            # Pas de consensus
            if len(sequences) == 2:
                # Exactement 2 comptages différents → pas de consensus
                return None
            else:
                # Plus de 2 comptages : conserver le résultat actuel s'il existe
                return current_result

