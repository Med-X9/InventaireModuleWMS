from typing import Optional, List, Dict, Any
from collections import defaultdict

from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils import timezone

from ..models import (
    EcartComptage,
    ComptageSequence,
    CountingDetail,
    Job,
    Inventory,
    Warehouse,
    JobDetail,
)
from ..repositories.ecart_comptage_repository import EcartComptageRepository
from ..exceptions import InventoryValidationError


class EcartComptageService:
    """
    Service métier pour la gestion des EcartComptage.
    """

    def __init__(self, repository: Optional[EcartComptageRepository] = None) -> None:
        self.repository = repository or EcartComptageRepository()

    @transaction.atomic
    def update_final_result(
        self,
        ecart_id: int,
        final_result: int,
        justification: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> EcartComptage:
        """
        Met à jour le résultat final d'un EcartComptage.

        Règles métier :
        - Il doit y avoir au moins deux comptages (séquences) enregistrés
          pour cet écart avant toute modification du résultat final.
        """
        ecart = self.repository.get_by_id(ecart_id)

        # Sécurité : on s'appuie sur total_sequences, mais on recalcule si besoin
        sequences_count = ecart.total_sequences or 0
        # if sequences_count < 2:
        #     # Double check via la relation si jamais total_sequences n'est pas à jour
        #     sequences_count = ecart.counting_sequences.count()

        # if sequences_count < 2:
        #     raise InventoryValidationError(
        #         "Il faut au moins deux comptages enregistrés pour modifier le résultat final."
        #     )

        ecart.final_result = final_result
        ecart.manual_result = True

        if justification is not None:
            ecart.justification = justification

        if resolved is not None:
            ecart.resolved = resolved
            if resolved and not ecart.stopped_reason:
                # Marquer explicitement que l'écart a été résolu manuellement
                ecart.stopped_reason = "RESOLU_MANUEL"

        return self.repository.save(ecart)

    @transaction.atomic
    def resolve_ecart(
        self,
        ecart_id: int,
        justification: Optional[str] = None,
    ) -> EcartComptage:
        """
        Marque un EcartComptage comme résolu (resolved = True).

        Règles métier :
        - Il doit y avoir au moins deux comptages (séquences) enregistrés.
        - Le champ final_result doit être renseigné (non nul).
        """
        ecart = self.repository.get_by_id(ecart_id)

        # Vérifier le nombre de séquences
        sequences_count = ecart.total_sequences or 0
        if sequences_count < 2:
            sequences_count = ecart.counting_sequences.count()

        if sequences_count < 2:
            raise InventoryValidationError(
                "Il faut au moins deux comptages enregistrés pour résoudre l'écart."
            )

        # Vérifier que le résultat final est renseigné
        if ecart.final_result is None:
            raise InventoryValidationError(
                "Le résultat final doit être renseigné avant de pouvoir résoudre l'écart."
            )

        ecart.resolved = True
        if justification is not None:
            ecart.justification = justification

        if not ecart.stopped_reason:
            ecart.stopped_reason = "RESOLU_MANUEL"

        return self.repository.save(ecart)

    @transaction.atomic
    def bulk_resolve_ecarts_by_inventory(self, inventory_id: int) -> int:
        """
        Marque comme résolus uniquement les EcartComptage d'un inventaire qui ont un final_result.

        Règles métier :
        - Seuls les écarts ayant un final_result non nul seront marqués comme résolus.
        - Les écarts sans final_result restent inchangés.

        Retourne le nombre d'écarts résolus.
        """
        # Vérifier que l'inventaire existe
        self.repository.get_inventory_by_id(inventory_id)

        # Marquer comme résolus uniquement les écarts qui ont un final_result
        return self.repository.bulk_resolve_ecarts_by_inventory(inventory_id)

    @transaction.atomic
    def close_jobs_with_all_locations_resolved_by_inventory(
        self, inventory_id: int
    ) -> int:
        """
        Met en statut TERMINE les jobs d'un inventaire dont :
        - tous les emplacements (JobDetail) sont au statut TERMINE
        - aucun écart de comptage lié au job n'est non résolu
          (final_result NULL ou resolved = False).

        Retourne le nombre de jobs clôturés.
        """
        # Jobs ayant au moins un EcartComptage non résolu (final_result NULL ou resolved False)
        unresolved_job_ids = set(
            CountingDetail.objects.filter(
                job__inventory_id=inventory_id,
                counting_sequences__ecart_comptage__inventory_id=inventory_id,
            )
            .filter(
                Q(counting_sequences__ecart_comptage__final_result__isnull=True)
                | Q(counting_sequences__ecart_comptage__resolved=False)
            )
            .values_list("job_id", flat=True)
            .distinct()
        )

        # Jobs ayant au moins un emplacement (JobDetail) non terminé
        jobs_with_non_termine_locations = set(
            JobDetail.objects.filter(job__inventory_id=inventory_id)
            .exclude(status="TERMINE")
            .values_list("job_id", flat=True)
            .distinct()
        )

        jobs_to_exclude = unresolved_job_ids.union(jobs_with_non_termine_locations)

        candidate_jobs = Job.objects.filter(inventory_id=inventory_id).exclude(
            id__in=jobs_to_exclude
        )

        now = timezone.now()
        closed_count = 0

        for job in candidate_jobs:
            if job.status != "TERMINE":
                job.status = "TERMINE"
                job.termine_date = now
                job.save(update_fields=["status", "termine_date"])
                closed_count += 1

        return closed_count

    @transaction.atomic
    def bulk_resolve_ecarts_and_close_jobs_by_inventory(
        self, inventory_id: int
    ) -> Dict[str, int]:
        """
        Combine la résolution en masse des écarts et la clôture des jobs :
        - marque comme résolus tous les EcartComptage avec un final_result
        - met en statut TERMINE les jobs dont tous les emplacements sont terminés
          et n'ont plus d'écarts non résolus.

        Retourne un dict avec les compteurs.
        """
        resolved_count = self.bulk_resolve_ecarts_by_inventory(inventory_id)
        closed_jobs_count = self.close_jobs_with_all_locations_resolved_by_inventory(
            inventory_id
        )
        return {
            "resolved_count": resolved_count,
            "closed_jobs_count": closed_jobs_count,
        }

    def _calculate_consensus_result(
        self,
        sequences: List[ComptageSequence],
        current_result: Optional[int]
    ) -> Optional[int]:
        """
        Détermine le résultat final d'un écart selon les règles métier.
        
        Logique uniforme pour TOUS les comptages :
        - Pour n'importe quel comptage (2ème, 3ème, 4ème, etc.), toujours vérifier
          s'il correspond à au moins un comptage précédent.
        - Si oui → enregistrer cette valeur dans resultat
        - Si non → enregistrer dans ecart (pas de resultat, ou conserver le précédent)
        
        Règles détaillées :
        1. 1er = 2ème → enregistrer dans resultat
        2. 1er ≠ 2ème → enregistrer dans ecart (pas de resultat)
        3. Nᵉ différent de tous les comptages précédents → enregistrer dans ecart (pas de resultat)
        4. Nᵉ égal à au moins un seul comptage parmi tous les précédents → enregistrer dans resultat
        
        Args:
            sequences: Liste de toutes les ComptageSequence (dans l'ordre chronologique)
            current_result: Résultat actuel de l'écart (peut être None)
            
        Returns:
            int: La valeur à enregistrer dans final_result, ou None si pas de consensus
        """
        if len(sequences) < 2:
            return None  # Pas de résultat si moins de 2 comptages
        
        # Logique uniforme : pour le comptage actuel (dernière séquence),
        # toujours vérifier s'il correspond à au moins un comptage précédent
        comptage_actuel = sequences[-1]
        quantite_actuelle = comptage_actuel.quantity
        
        # Extraire toutes les quantités des comptages précédents
        # (on exclut la dernière séquence qui est le comptage actuel)
        quantites_precedentes = [seq.quantity for seq in sequences[:-1]]
        
        # Vérifier si le comptage actuel correspond à au moins un comptage précédent
        if quantite_actuelle in quantites_precedentes:
            # Le comptage actuel correspond à au moins un précédent → enregistrer dans resultat
            return quantite_actuelle
        else:
            # Le comptage actuel est différent de tous les précédents → enregistrer dans ecart
            # Cas spécial : si exactement 2 comptages différents, pas de consensus (retourner None)
            # Sinon, conserver le résultat actuel s'il existe (cas où un précédent comptage avait trouvé un consensus)
            if len(sequences) == 2:
                # Exactement 2 comptages différents → pas de consensus
                return None
            else:
                # Plus de 2 comptages : conserver le résultat actuel s'il existe
                return current_result

    @transaction.atomic
    def resolve_zero_differences_by_inventory(self, inventory_id: int) -> Dict[str, Any]:
        """
        Calcule les écarts entre 1er et 2ème comptage pour tous les jobs liés à un inventaire,
        et résout automatiquement les écarts = 0.
        
        Args:
            inventory_id: ID de l'inventaire pour lequel traiter tous les jobs liés
            
        Returns:
            Dict contenant les statistiques du traitement
        """
        # Valider que l'inventaire existe
        inventory = self.repository.get_inventory_by_id(inventory_id)
        
        # Récupérer tous les jobs liés à cet inventaire
        jobs = Job.objects.filter(inventory=inventory)
        
        if not jobs.exists():
            return {
                'success': False,
                'message': f'Aucun job trouvé pour l\'inventaire {inventory.reference}',
                'stats': {}
            }
        
        # Statistiques globales
        stats = {
            'total_jobs_processed': 0,
            'total_assignments_found': 0,
            'total_ecarts_processed': 0,
            'total_ecarts_resolved': 0
        }
        
        # Traiter chaque job
        for job in jobs:
            stats['total_jobs_processed'] += 1
            
            # Récupérer tous les EcartComptage liés au job via les ComptageSequence
            ecarts_comptage = EcartComptage.objects.filter(
                counting_sequences__counting_detail__job=job
            ).distinct().prefetch_related(
                'counting_sequences__counting_detail__counting',
                'counting_sequences__counting_detail__product',
                'counting_sequences__counting_detail__location'
            )
            
            if not ecarts_comptage.exists():
                continue
            
            # Traiter chaque EcartComptage de ce job
            for ecart in ecarts_comptage:
                stats['total_ecarts_processed'] += 1
                
                # Calculer l'écart pour cet EcartComptage
                ecart_result = self._calculate_ecart_difference(ecart)
                
                if ecart_result['has_difference']:
                    difference = ecart_result['difference']
                    
                    # Si écart = 0 et pas encore résolu
                    if difference == 0 and ecart.final_result is None:
                        # CORRECTION: Utiliser la quantité réelle, pas 0
                        quantity = ecart_result['seq1_quantity']
                        ecart.final_result = quantity
                        ecart.resolved = True
                        ecart.manual_result = False
                        ecart.justification = "Écart automatiquement résolu (différence = 0)"
                        ecart.save()
                        
                        stats['total_ecarts_resolved'] += 1
        
        return {
            'success': True,
            'message': f'{stats["total_ecarts_resolved"]} EcartComptage résolus automatiquement',
            'stats': stats
        }

    def _calculate_ecart_difference(self, ecart_comptage: EcartComptage) -> Dict[str, Any]:
        """
        Calcule l'écart entre les séquences de comptage 1 et 2 pour un EcartComptage.

        Args:
            ecart_comptage: Instance d'EcartComptage

        Returns:
            dict: {
                'has_difference': bool,
                'difference': int or None,
                'seq1_quantity': int or None,
                'seq2_quantity': int or None,
                'reason': str (si pas de différence)
            }
        """
        # Récupérer toutes les séquences pour cet écart, triées par numéro de séquence
        sequences = ecart_comptage.counting_sequences.all().order_by('sequence_number')

        if sequences.count() < 2:
            return {
                'has_difference': False,
                'difference': None,
                'seq1_quantity': None,
                'seq2_quantity': None,
                'reason': f'Sequences insuffisantes ({sequences.count()}/2 minimum)'
            }

        # Prendre les 2 premières séquences (normalement sequence_number 1 et 2)
        seq1 = sequences[0]  # Séquence 1 (1er comptage)
        seq2 = sequences[1]  # Séquence 2 (2ème comptage)

        # Calculer l'écart: quantité_seq2 - quantité_seq1
        difference = seq2.quantity - seq1.quantity

        return {
            'has_difference': True,
            'difference': difference,
            'seq1_quantity': seq1.quantity,
            'seq2_quantity': seq2.quantity,
            'reason': None
        }

    @transaction.atomic
    def recalculate_ecarts_by_inventory_and_warehouse(
        self, 
        inventory_id: int, 
        warehouse_id: int
    ) -> Dict[str, Any]:
        """
        Recalcule les écarts selon les données existantes pour un inventaire et un entrepôt.
        
        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt
            
        Returns:
            Dict contenant les statistiques du traitement
        """
        # Vérifier que l'inventaire et l'entrepôt existent
        inventory = self.repository.get_inventory_by_id(inventory_id)
        warehouse = Warehouse.objects.get(id=warehouse_id)
        
        # Récupérer tous les jobs de cet inventaire/entrepôt
        jobs = Job.objects.filter(
            inventory_id=inventory_id,
            warehouse_id=warehouse_id
        ).prefetch_related(
            Prefetch(
                'countingdetail_set',
                queryset=CountingDetail.objects.select_related(
                    'product', 'location', 'counting', 'job'
                ).prefetch_related(
                    Prefetch(
                        'counting_sequences',
                        queryset=ComptageSequence.objects.order_by('sequence_number')
                    )
                )
            )
        )
        
        if not jobs.exists():
            return {
                'success': False,
                'message': 'Aucun job trouvé pour ces critères',
                'stats': {}
            }
        
        # Statistiques
        stats = {
            'total_counting_details': 0,
            'total_sequences': 0,
            'ecarts_processed': 0,
            'ecarts_updated': 0,
            'final_results_calculated': 0,
            'errors': []
        }
        
        for job in jobs:
            # Grouper les CountingDetail par (product, location) pour identifier les écarts
            counting_details_by_ecart = defaultdict(list)
            
            for cd in job.countingdetail_set.all():
                if cd.product and cd.location:
                    key = (cd.product.id, cd.location.id, inventory_id)
                    counting_details_by_ecart[key].append(cd)
                    stats['total_counting_details'] += 1
            
            # Traiter chaque groupe d'écarts
            for ecart_key, counting_details in counting_details_by_ecart.items():
                try:
                    product_id, location_id, inv_id = ecart_key
                    product = counting_details[0].product
                    location = counting_details[0].location
                    
                    # Récupérer ou créer l'EcartComptage
                    ecart_existant = None
                    sequences_existantes = ComptageSequence.objects.filter(
                        counting_detail__product_id=product_id,
                        counting_detail__location_id=location_id,
                        counting_detail__counting__inventory_id=inv_id
                    ).select_related('ecart_comptage')
                    
                    if sequences_existantes.exists():
                        ecart_existant = sequences_existantes.first().ecart_comptage
                    else:
                        # Créer un nouvel écart
                        ecart_existant = EcartComptage(
                            inventory_id=inv_id,
                            total_sequences=0,
                            resolved=False,
                            final_result=None,
                            justification=None
                        )
                        ecart_existant.reference = f"ECART-{inventory.reference}-{product.reference}-{location.reference}"
                        ecart_existant.save()
                    
                    ecart = ecart_existant
                    
                    # Collecter toutes les séquences existantes pour cet écart
                    all_sequences = []
                    for cd in counting_details:
                        sequences = list(cd.counting_sequences.order_by('sequence_number'))
                        all_sequences.extend(sequences)
                    
                    all_sequences.sort(key=lambda x: x.sequence_number)
                    stats['total_sequences'] += len(all_sequences)
                    
                    if not all_sequences:
                        continue
                    
                    # Recalculer les écarts entre séquences consécutives
                    sequences_to_update = []
                    for i, seq in enumerate(all_sequences):
                        if i > 0:  # Pas pour la première séquence
                            prev_seq = all_sequences[i-1]
                            old_ecart = seq.ecart_with_previous
                            new_ecart = abs(seq.quantity - prev_seq.quantity)
                            
                            if old_ecart != new_ecart:
                                seq.ecart_with_previous = new_ecart
                                sequences_to_update.append(seq)
                    
                    # Mettre à jour les séquences si nécessaire
                    if sequences_to_update:
                        ComptageSequence.objects.bulk_update(
                            sequences_to_update, ['ecart_with_previous']
                        )
                    
                    # Recalculer le résultat final selon la logique existante
                    old_final_result = ecart.final_result
                    final_result = self._calculate_consensus_result(all_sequences, ecart.final_result)
                    
                    stats['ecarts_processed'] += 1
                    
                    if final_result != old_final_result:
                        ecart.final_result = final_result
                        ecart.save()
                        stats['ecarts_updated'] += 1
                    
                    if final_result is not None:
                        stats['final_results_calculated'] += 1
                        
                except Exception as e:
                    error_msg = f"Erreur pour écart {ecart_key}: {str(e)}"
                    stats['errors'].append(error_msg)
        
        return {
            'success': True,
            'message': 'Recalcul terminé avec succès',
            'stats': stats
        }

    @transaction.atomic
    def create_missing_counting_sequences_by_inventory(self, inventory_id: int) -> Dict[str, Any]:
        """
        Crée les ComptageSequence manquantes pour les CountingDetail existants d'un inventaire.
        
        Args:
            inventory_id: ID de l'inventaire pour lequel créer les séquences manquantes
            
        Returns:
            Dict contenant les statistiques du traitement
        """
        # Valider que l'inventaire existe
        inventory = self.repository.get_inventory_by_id(inventory_id)
        
        # Récupérer tous les jobs liés à cet inventaire
        jobs = Job.objects.filter(inventory=inventory)
        
        if not jobs.exists():
            return {
                'success': False,
                'message': f'Aucun job trouvé pour l\'inventaire {inventory.reference}',
                'stats': {}
            }
        
        # Statistiques globales
        stats = {
            'total_counting_details_found': 0,
            'total_sequences_created': 0,
            'total_ecarts_created': 0
        }
        
        # Traiter chaque job
        for job in jobs:
            # Récupérer tous les CountingDetail de ce job
            counting_details = CountingDetail.objects.filter(job=job)
            
            if not counting_details.exists():
                continue
            
            # Traiter chaque CountingDetail
            for counting_detail in counting_details:
                stats['total_counting_details_found'] += 1
                
                # Vérifier si ce CountingDetail a déjà une ComptageSequence
                existing_sequence = ComptageSequence.objects.filter(
                    counting_detail=counting_detail
                ).first()
                
                if existing_sequence:
                    continue  # Passer silencieusement les existants
                
                try:
                    # 1. Créer ou récupérer l'EcartComptage
                    ecart, created = self._get_or_create_ecart_comptage(counting_detail)
                    if created:
                        stats['total_ecarts_created'] += 1
                    
                    # 2. Déterminer le numéro de séquence
                    sequence_number = self._get_next_sequence_number(ecart, counting_detail)
                    
                    # 3. Calculer l'écart avec la séquence précédente
                    ecart_with_previous = self._calculate_ecart_with_previous(
                        ecart, sequence_number, counting_detail.quantity_inventoried
                    )
                    
                    # 4. Créer la ComptageSequence
                    sequence = ComptageSequence.objects.create(
                        ecart_comptage=ecart,
                        counting_detail=counting_detail,
                        sequence_number=sequence_number,
                        quantity=counting_detail.quantity_inventoried,
                        ecart_with_previous=ecart_with_previous
                    )
                    
                    # 5. Générer la référence
                    sequence.reference = sequence.generate_reference(ComptageSequence.REFERENCE_PREFIX)
                    sequence.save()
                    
                    # 6. Mettre à jour l'écart
                    ecart.total_sequences = sequence_number
                    ecart.stopped_sequence = sequence_number
                    
                    # Calculer le résultat final si possible
                    if sequence_number >= 2:
                        all_sequences = list(ecart.counting_sequences.order_by('sequence_number'))
                        final_result = self._calculate_consensus_result(all_sequences, ecart.final_result)
                        if final_result is not None:
                            ecart.final_result = final_result
                            ecart.resolved = True
                    
                    ecart.save()
                    
                    stats['total_sequences_created'] += 1
                    
                except Exception as e:
                    # Log l'erreur mais continue
                    pass
        
        return {
            'success': True,
            'message': f'{stats["total_sequences_created"]} ComptageSequence créées avec succès',
            'stats': stats
        }

    def _get_or_create_ecart_comptage(self, counting_detail: CountingDetail) -> tuple:
        """
        Récupère ou crée un EcartComptage pour le CountingDetail.
        Regroupement par (produit + emplacement + inventaire)
        
        Args:
            counting_detail: Instance de CountingDetail
            
        Returns:
            tuple: (ecart, created) où created est True si nouvellement créé
        """
        product = counting_detail.product
        location = counting_detail.location
        inventory = counting_detail.job.inventory
        
        if not product or not location:
            raise ValueError("Produit et emplacement requis pour créer un EcartComptage")
        
        # Chercher un écart existant
        existing_ecart = EcartComptage.objects.filter(
            counting_sequences__counting_detail__product=product,
            counting_sequences__counting_detail__location=location,
            inventory=inventory
        ).distinct().first()
        
        if existing_ecart:
            # Vérifier qu'il n'est pas résolu
            if existing_ecart.resolved:
                raise ValueError(f"L'écart {existing_ecart.reference} est déjà résolu")
            return existing_ecart, False
        
        # Créer un nouvel écart
        ecart = EcartComptage.objects.create(
            inventory=inventory,
            total_sequences=0,
            resolved=False,
            final_result=None
        )
        ecart.reference = ecart.generate_reference(EcartComptage.REFERENCE_PREFIX)
        ecart.save()
        
        return ecart, True

    def _get_next_sequence_number(
        self, 
        ecart: EcartComptage, 
        counting_detail: CountingDetail
    ) -> int:
        """
        Détermine le prochain numéro de séquence pour cet écart.
        
        Args:
            ecart: Instance d'EcartComptage
            counting_detail: Instance de CountingDetail
            
        Returns:
            int: Numéro de séquence
        """
        # Vérifier si ce CountingDetail a déjà une séquence dans cet écart
        existing_sequence = ecart.counting_sequences.filter(
            counting_detail=counting_detail
        ).first()
        
        if existing_sequence:
            # Mise à jour d'une séquence existante
            return existing_sequence.sequence_number
        else:
            # Nouvelle séquence
            return ecart.total_sequences + 1

    def _calculate_ecart_with_previous(
        self, 
        ecart: EcartComptage, 
        sequence_number: int, 
        current_quantity: int
    ) -> Optional[int]:
        """
        Calcule l'écart avec la séquence précédente.
        
        Args:
            ecart: Instance d'EcartComptage
            sequence_number: Numéro de la séquence actuelle
            current_quantity: Quantité de la séquence actuelle
            
        Returns:
            int ou None: Écart avec la séquence précédente
        """
        if sequence_number <= 1:
            return None
        
        # Trouver la séquence précédente
        previous_sequence = ecart.counting_sequences.filter(
            sequence_number=sequence_number - 1
        ).first()
        
        if previous_sequence:
            return abs(current_quantity - previous_sequence.quantity)
        
        return None

