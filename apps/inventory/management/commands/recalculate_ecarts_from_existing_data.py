"""
Commande Django pour recalculer les écarts selon les données existantes en base.
Utilise la même logique que le système existant pour inventory_id=1 et warehouse_id=1.

Usage: python manage.py recalculate_ecarts_from_existing_data --inventory-id 1 --warehouse-id 1 [--dry-run]
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Prefetch
from typing import Dict, List, Any, Optional
from collections import defaultdict

from apps.inventory.models import (
    Inventory, Warehouse, Job, CountingDetail, EcartComptage,
    ComptageSequence, Counting
)


class Command(BaseCommand):
    help = 'Recalcule les écarts selon les données existantes pour inventory_id=1 et warehouse_id=1'

    def add_arguments(self, parser):
        parser.add_argument(
            '--inventory-id',
            type=int,
            default=1,
            help='ID de l\'inventaire (défaut: 1)',
        )
        parser.add_argument(
            '--warehouse-id',
            type=int,
            default=1,
            help='ID de l\'entrepôt (défaut: 1)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : affiche ce qui serait fait sans modifier la base de données',
        )

    def handle(self, *args, **options):
        inventory_id = options['inventory_id']
        warehouse_id = options['warehouse_id']
        dry_run = options['dry_run']

        self.stdout.write('🔄 Recalcul des écarts selon données existantes')
        self.stdout.write(f'  🔍 Inventaire ID: {inventory_id}')
        self.stdout.write(f'  🔍 Entrepôt ID: {warehouse_id}')

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODE DRY-RUN : Aucune modification ne sera effectuée'))

        try:
            # Vérifier que l'inventaire et l'entrepôt existent
            inventory = Inventory.objects.get(id=inventory_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)

            self.stdout.write(f'  ✅ Inventaire: {inventory.reference}')
            self.stdout.write(f'  ✅ Entrepôt: {warehouse.reference}')

        except Inventory.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Inventaire {inventory_id} non trouvé'))
            return
        except Warehouse.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Entrepôt {warehouse_id} non trouvé'))
            return

        # Récupérer toutes les données pertinentes en une seule requête optimisée
        self.stdout.write('\n  📊 Récupération des données existantes...')

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

        total_jobs = jobs.count()
        self.stdout.write(f'  ✅ {total_jobs} job(s) trouvé(s)')

        if total_jobs == 0:
            self.stdout.write(self.style.WARNING('⚠️  Aucun job trouvé pour ces critères'))
            return

        # Analyser et recalculer les écarts
        stats = {
            'total_counting_details': 0,
            'total_sequences': 0,
            'ecarts_processed': 0,
            'ecarts_updated': 0,
            'final_results_calculated': 0,
            'errors': []
        }

        if dry_run:
            self.stdout.write('\n' + '='*80)
            self.stdout.write('SIMULATION - Recalcul des écarts:')
            self.stdout.write('='*80)

        for job in jobs:
            self.stdout.write(f'\n📦 TRAITEMENT JOB: {job.reference} (ID: {job.id})')

            # Grouper les CountingDetail par (product, location) pour identifier les écarts
            counting_details_by_ecart = defaultdict(list)

            for cd in job.countingdetail_set.all():
                if cd.product and cd.location:
                    key = (cd.product.id, cd.location.id, inventory_id)
                    counting_details_by_ecart[key].append(cd)
                    stats['total_counting_details'] += 1
                else:
                    self.stdout.write(f'  ⚠️  CountingDetail {cd.id} ignoré: produit ou emplacement manquant')

            total_ecarts_in_job = len(counting_details_by_ecart)
            self.stdout.write(f'  🔍 {total_ecarts_in_job} écart(s) identifié(s) dans ce job')

            # Traiter chaque groupe d'écarts
            for ecart_key, counting_details in counting_details_by_ecart.items():
                try:
                    product_id, location_id, inv_id = ecart_key
                    product = counting_details[0].product
                    location = counting_details[0].location

                    self.stdout.write(f'\n    🎯 TRAITEMENT ÉCART: {product.reference} @ {location.reference}')
                    self.stdout.write(f'       Produit: {product.Short_Description} (ID: {product.id})')
                    self.stdout.write(f'       Emplacement: {location.location_reference} (ID: {location.id})')

                    # Récupérer ou créer l'EcartComptage - Logique identique à CountingDetailService
                    # Chercher un EcartComptage existant via les ComptageSequence
                    ecart_existant = None
                    sequences_existantes = ComptageSequence.objects.filter(
                        counting_detail__product_id=product_id,
                        counting_detail__location_id=location_id,
                        counting_detail__counting__inventory_id=inv_id
                    ).select_related('ecart_comptage')

                    if sequences_existantes.exists():
                        # Récupérer l'écart existant
                        ecart_existant = sequences_existantes.first().ecart_comptage
                        self.stdout.write(f'       📋 EcartComptage existant trouvé: {ecart_existant.reference}')
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
                        if not dry_run:
                            ecart_existant.save()
                        self.stdout.write(f'       🆕 EcartComptage créé: {ecart_existant.reference}')

                    ecart = ecart_existant

                    # Collecter toutes les séquences existantes pour cet écart
                    all_sequences = []
                    for cd in counting_details:
                        sequences = list(cd.counting_sequences.order_by('sequence_number'))
                        all_sequences.extend(sequences)
                        self.stdout.write(f'       📄 CountingDetail {cd.id}: {len(sequences)} séquence(s)')

                    all_sequences.sort(key=lambda x: x.sequence_number)
                    stats['total_sequences'] += len(all_sequences)

                    self.stdout.write(f'       📊 TOTAL: {len(all_sequences)} séquence(s) pour cet écart')

                    if not all_sequences:
                        self.stdout.write('       ⚠️  AUCUNE SÉQUENCE - Écart ignoré')
                        continue

                    # Afficher les détails de chaque séquence
                    self.stdout.write('       📋 DÉTAIL DES SÉQUENCES:')
                    for seq in all_sequences:
                        self.stdout.write(f'          • Séqu.{seq.sequence_number}: qty={seq.quantity}, écart_précédent={seq.ecart_with_previous}')

                    # Recalculer les écarts entre séquences consécutives
                    self.stdout.write('       🔄 RECALCUL DES ÉCARTS ENTRE SÉQUENCES:')
                    sequences_to_update = []
                    for i, seq in enumerate(all_sequences):
                        if i > 0:  # Pas pour la première séquence
                            prev_seq = all_sequences[i-1]
                            old_ecart = seq.ecart_with_previous
                            new_ecart = abs(seq.quantity - prev_seq.quantity)

                            if old_ecart != new_ecart:
                                self.stdout.write(f'          🔄 Séqu.{seq.sequence_number}: écart {old_ecart} → {new_ecart}')
                                seq.ecart_with_previous = new_ecart
                                sequences_to_update.append(seq)
                            else:
                                self.stdout.write(f'          ✅ Séqu.{seq.sequence_number}: écart inchangé ({old_ecart})')
                        else:
                            self.stdout.write(f'          📍 Séqu.{seq.sequence_number}: première séquence (pas d\'écart)')

                    # Mettre à jour les séquences si nécessaire
                    if not dry_run and sequences_to_update:
                        ComptageSequence.objects.bulk_update(
                            sequences_to_update, ['ecart_with_previous']
                        )
                        self.stdout.write(f'       💾 {len(sequences_to_update)} séquence(s) mise(s) à jour en base')

                    # Recalculer le résultat final selon la logique existante
                    self.stdout.write('       🎯 CALCUL DU RÉSULTAT FINAL:')
                    old_final_result = ecart.final_result
                    final_result = self._calculate_consensus_result(all_sequences, ecart.final_result)

                    self.stdout.write(f'          Ancien final_result: {old_final_result}')
                    self.stdout.write(f'          Nouveau final_result: {final_result}')

                    # Analyser le consensus
                    if len(all_sequences) >= 2:
                        dernier_comptage = all_sequences[-1]
                        quantite_actuelle = dernier_comptage.quantity
                        quantites_precedentes = [seq.quantity for seq in all_sequences[:-1]]

                        self.stdout.write(f'          Dernier comptage: quantité {quantite_actuelle}')
                        self.stdout.write(f'          Quantités précédentes: {quantites_precedentes}')

                        if quantite_actuelle in quantites_precedentes:
                            self.stdout.write('          ✅ CONSENSUS TROUVÉ - Quantité validée')
                        else:
                            self.stdout.write('          ❌ PAS DE CONSENSUS - Résultat actuel conservé')
                    else:
                        self.stdout.write('          ⚠️  MOINS DE 2 SÉQUENCES - Pas de consensus possible')

                    stats['ecarts_processed'] += 1

                    if final_result != old_final_result:
                        if dry_run:
                            self.stdout.write(f'       📈 FINAL_RESULT: {old_final_result} → {final_result} (DRY-RUN)')
                        else:
                            ecart.final_result = final_result
                            ecart.save()
                            stats['ecarts_updated'] += 1
                            self.stdout.write(f'       ✅ FINAL_RESULT MIS À JOUR: {old_final_result} → {final_result}')
                    else:
                        self.stdout.write(f'       ✅ FINAL_RESULT INCHANGÉ: {final_result}')

                    if final_result is not None:
                        stats['final_results_calculated'] += 1
                        self.stdout.write(f'       🎉 ÉCART RÉSOLU AUTOMATIQUEMENT')
                    else:
                        self.stdout.write(f'       ⏳ RÉSOLUTION MANUELLE REQUISE')

                except Exception as e:
                    error_msg = f"Erreur pour écart {ecart_key}: {str(e)}"
                    stats['errors'].append(error_msg)
                    self.stdout.write(self.style.ERROR(f'    ❌ ERREUR: {error_msg}'))
                    import traceback
                    self.stdout.write(self.style.ERROR(f'       Traceback: {traceback.format_exc()}'))

            self.stdout.write(f'  ✅ JOB {job.reference} TRAITÉ: {total_ecarts_in_job} écart(s)')

        # Résumé final
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('📊 RÉSUMÉ DU RECALCUL'))
        self.stdout.write('='*80)
        self.stdout.write(f"  Jobs traités: {total_jobs}")
        self.stdout.write(f"  CountingDetails analysés: {stats['total_counting_details']}")
        self.stdout.write(f"  ComptageSequence trouvées: {stats['total_sequences']}")
        self.stdout.write(f"  Écarts traités: {stats['ecarts_processed']}")
        self.stdout.write(f"  Écarts mis à jour: {stats['ecarts_updated']}")
        self.stdout.write(f"  Résultats finaux calculés: {stats['final_results_calculated']}")

        if stats['errors']:
            self.stdout.write(self.style.ERROR(f"\n  ❌ Erreurs: {len(stats['errors'])}"))
            for error in stats['errors'][:5]:
                self.stdout.write(self.style.ERROR(f"    - {error}"))
            if len(stats['errors']) > 5:
                self.stdout.write(self.style.ERROR(f"    ... et {len(stats['errors']) - 5} autres"))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  MODE DRY-RUN : Aucune donnée modifiée'))
            self.stdout.write('💡 Relancer sans --dry-run pour appliquer les modifications')
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Recalcul terminé avec succès!'))

    def _calculate_consensus_result(self, sequences: List[ComptageSequence], current_result: Optional[int]) -> Optional[int]:
        """
        Logique identique à CountingDetailService._calculate_consensus_result
        Détermine le résultat final selon les règles métier existantes.
        """
        if len(sequences) < 2:
            return None  # Pas de résultat si moins de 2 comptages

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
            # Pas de consensus → conserver le résultat actuel
            return current_result
