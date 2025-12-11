"""
Commande Django pour clôturer les assignments si l'autre assignment est déjà clôturé.

Cette commande :
- Récupère les assignments avec counting order 1 ou 2 qui ne sont pas TERMINE
- Pour chaque assignment, vérifie que tous les emplacements qui ont des JobDetail ont aussi des CountingDetail
- Vérifie que le total des JobDetail est < 8 pour le counting order (1 ou 2)
- Si oui, FORCE tous les JobDetail non TERMINE à TERMINE
- Clôture l'assignment
- Synchronise les CountingDetail entre les deux countings
- Vérifie si tous les assignments du job sont TERMINE
- Vérifie si tous les EcartComptage de l'inventaire ont un final_result non null
- Clôture le job si toutes les conditions sont remplies

Exemple d'utilisation:
    python manage.py close_assignments_if_other_terminated --inventory-id 2 --warehouse-id 1
    python manage.py close_assignments_if_other_terminated --inventory-id 2 --warehouse-id 1 --dry-run
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from typing import Optional, Tuple
from collections import defaultdict
import logging

from apps.inventory.models import Assigment, JobDetail, Job, CountingDetail, EcartComptage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clôture les assignments si tous les emplacements JobDetail ont des CountingDetail et total JobDetail < 8'

    def add_arguments(self, parser):
        parser.add_argument(
            '--inventory-id',
            type=int,
            required=True,
            help='ID de l\'inventaire',
        )
        parser.add_argument(
            '--warehouse-id',
            type=int,
            required=True,
            help='ID de l\'entrepôt',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : affiche ce qui sera fait sans modifier la base de données',
        )

    def handle(self, *args, **options):
        inventory_id = options['inventory_id']
        warehouse_id = options['warehouse_id']
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS('📋 Clôture des assignments si tous les emplacements JobDetail ont des CountingDetail (JobDetail < 8)'))
        self.stdout.write(f'  🔍 Inventaire ID: {inventory_id}')
        self.stdout.write(f'  🔍 Entrepôt ID: {warehouse_id}')
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODE DRY-RUN : Aucune modification ne sera effectuée'))
        
        # Récupérer les assignments avec counting order 1 ou 2 qui ne sont pas TERMINE
        assignments = Assigment.objects.filter(
            counting__order__in=[1, 2],
            job__inventory_id=inventory_id,
            job__warehouse_id=warehouse_id
        ).exclude(
            status='TERMINE'
        ).select_related(
            'job',
            'job__inventory',
            'job__warehouse',
            'counting'
        ).order_by('counting__order', 'job_id')
        
        total_assignments = assignments.count()
        self.stdout.write(f'  ✅ {total_assignments} assignment(s) trouvé(s) (counting order 1 ou 2, non TERMINE)')
        
        if total_assignments == 0:
            self.stdout.write(self.style.WARNING('⚠️  Aucun assignment à traiter'))
            return
        
        # Statistiques
        stats = {
            'total_assignments_found': total_assignments,
            'total_processed': 0,
            'assignments_closed': 0,
            'assignments_skipped_missing_counting_details': 0,
            'assignments_skipped_too_many_job_details': 0,
            'jobs_closed': 0,
            'jobs_already_terminated': 0,
            'job_details_forced_terminated': 0,
            'counting_details_synced': 0,
            'counting_details_created': 0,
            'jobs_processed': set(),
            'errors': []
        }
        
        if dry_run:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('SIMULATION - Ce qui sera fait:')
            self.stdout.write('='*60)
        
        # Traiter chaque assignment
        for assignment in assignments:
            try:
                # Vérifier si l'assignment est déjà TERMINE (ne devrait pas arriver avec le filtre, mais sécurité)
                if assignment.status == 'TERMINE':
                    continue
                
                result = self.process_assignment(assignment, dry_run)
                stats['total_processed'] += 1
                stats['assignments_closed'] += result['assignment_closed']
                stats['assignments_skipped_missing_counting_details'] += result.get('skipped_missing_counting_details', 0)
                stats['assignments_skipped_too_many_job_details'] += result.get('skipped_too_many_job_details', 0)
                stats['jobs_closed'] += result['job_closed']
                stats['job_details_forced_terminated'] += result.get('job_details_forced_terminated', 0)
                stats['counting_details_synced'] += result.get('counting_details_synced', 0)
                stats['counting_details_created'] += result.get('counting_details_created', 0)
                
                # Ajouter le job à la liste des jobs traités
                stats['jobs_processed'].add(assignment.job_id)
                
                # Vérifier si le job était déjà TERMINE avant traitement
                if result.get('job_already_terminated', False):
                    stats['jobs_already_terminated'] += 1
            except Exception as e:
                error_msg = f"Erreur lors du traitement de l'assignment {assignment.reference}: {str(e)}"
                stats['errors'].append(error_msg)
                self.stdout.write(self.style.ERROR(f'  ❌ {error_msg}'))
                logger.error(error_msg, exc_info=True)
        
        # Afficher le résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 RÉSUMÉ'))
        self.stdout.write('='*60)
        self.stdout.write(f"  Assignments trouvés: {stats['total_assignments_found']}")
        self.stdout.write(f"  Assignments traités: {stats['total_processed']}")
        self.stdout.write(f"  Assignments ignorés (emplacements sans CountingDetail): {stats['assignments_skipped_missing_counting_details']}")
        self.stdout.write(f"  Assignments ignorés (≥ 8 JobDetail): {stats['assignments_skipped_too_many_job_details']}")
        self.stdout.write(f"  Assignments clôturés: {stats['assignments_closed']}")
        self.stdout.write(f"  JobDetail forcés à TERMINE: {stats['job_details_forced_terminated']}")
        self.stdout.write('')
        self.stdout.write(f"  Jobs uniques traités: {len(stats['jobs_processed'])}")
        self.stdout.write(f"  Jobs clôturés: {stats['jobs_closed']}")
        self.stdout.write(f"  Jobs déjà TERMINE: {stats['jobs_already_terminated']}")
        self.stdout.write('')
        self.stdout.write(f"  Synchronisations CountingDetail: {stats['counting_details_synced']}")
        self.stdout.write(f"  CountingDetails créés: {stats['counting_details_created']}")
        
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f"\n  ❌ Erreurs: {len(stats['errors'])}"))
            for error in stats['errors']:
                self.stdout.write(self.style.ERROR(f"    - {error}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  MODE DRY-RUN : Aucune modification n\'a été effectuée'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Traitement terminé avec succès!'))
    
    @transaction.atomic
    def process_assignment(self, assignment: Assigment, dry_run: bool = False) -> dict:
        """
        Traite un assignment en vérifiant que tous les emplacements JobDetail ont des CountingDetail :
        0. Vérifie que tous les emplacements qui ont des JobDetail ont aussi des CountingDetail
        1. Vérifie que le total des JobDetail est < 8 pour le counting order
        2. Si oui, FORCE tous les JobDetail non TERMINE à TERMINE
        3. Clôture l'assignment
        4. Synchronise les CountingDetail entre les deux countings
        5. Vérifie si tous les assignments du job sont TERMINE
        6. Vérifie si tous les EcartComptage de l'inventaire ont un final_result non null
        7. Si les deux conditions précédentes sont remplies, clôture le job
        
        Args:
            assignment: L'assignment à traiter
            dry_run: Si True, ne fait que simuler les actions
            
        Returns:
            Dictionnaire avec les statistiques du traitement
        """
        result = {
            'assignment_closed': 0,
            'job_closed': 0,
            'job_already_terminated': 0,
            'skipped_missing_counting_details': 0,
            'skipped_too_many_job_details': 0,
            'job_details_forced_terminated': 0,
            'counting_details_synced': 0,
            'counting_details_created': 0
        }
        
        job = assignment.job
        counting = assignment.counting
        counting_order = counting.order
        now = timezone.now()
        
        self.stdout.write(
            f'\n📦 Assignment: {assignment.reference} '
            f'(Job: {job.reference}, Counting: {counting.reference}, Order: {counting_order})'
        )
        
        # 0. Vérifier que tous les emplacements qui ont des JobDetail ont aussi des CountingDetail
        job_details_all = JobDetail.objects.filter(
            job=job,
            counting=counting
        ).select_related('location')
        
        if not job_details_all.exists():
            result['skipped_missing_counting_details'] = 1
            self.stdout.write(
                self.style.WARNING(
                    f'  ⚠️  Assignment {assignment.reference} ignoré : '
                    f'Aucun JobDetail trouvé pour ce job et counting {counting_order}'
                )
            )
            return result
        
        # Récupérer les emplacements uniques qui ont des JobDetail
        locations_with_job_details = set(job_details_all.values_list('location_id', flat=True).distinct())
        
        # Vérifier que tous ces emplacements ont au moins un CountingDetail pour ce job et counting
        counting_details = CountingDetail.objects.filter(
            job=job,
            counting=counting
        ).values_list('location_id', flat=True).distinct()
        
        locations_with_counting_details = set(counting_details)
        
        # Vérifier si tous les emplacements avec JobDetail ont des CountingDetail
        missing_locations = locations_with_job_details - locations_with_counting_details
        
        if missing_locations:
            result['skipped_missing_counting_details'] = 1
            self.stdout.write(
                self.style.WARNING(
                    f'  ⚠️  Assignment {assignment.reference} ignoré : '
                    f'{len(missing_locations)} emplacement(s) avec JobDetail mais sans CountingDetail '
                    f'(sur {len(locations_with_job_details)} emplacement(s) total)'
                )
            )
            return result
        
        self.stdout.write(
            self.style.SUCCESS(
                f'  ✅ Tous les emplacements avec JobDetail ont des CountingDetail '
                f'({len(locations_with_job_details)} emplacement(s))'
            )
        )
        
        # 1. Vérifier que le total des JobDetail est < 8
        # Compter tous les JobDetail (pas seulement les emplacements uniques)
        total_job_details = JobDetail.objects.filter(
            job=job,
            counting=counting
        ).count()
        
        # Condition : total des JobDetail doit être < 8
        if total_job_details >= 8:
            result['skipped_too_many_job_details'] = 1
            self.stdout.write(
                self.style.WARNING(
                    f'  ⚠️  Assignment {assignment.reference} ignoré : '
                    f'{total_job_details} JobDetail(s) trouvé(s) '
                    f'(limite: < 8) pour le counting {counting_order}'
                )
            )
            return result
        
        # Récupérer tous les JobDetail (pas seulement distinct par location)
        job_details = JobDetail.objects.filter(
            job=job,
            counting=counting
        ).select_related('location')
        
        # 2. Si < 8, FORCER tous les JobDetail non TERMINE à TERMINE
        # IMPORTANT: Gérer les doublons (même job, même location, même counting)
        # Grouper les JobDetail par (location_id, counting_id) pour gérer les doublons
        job_details_by_location = defaultdict(list)
        for jd in job_details:
            key = (jd.location_id, jd.counting_id if jd.counting_id else None)
            job_details_by_location[key].append(jd)
        
        # Forcer tous les JobDetail non TERMINE à TERMINE
        job_details_to_update = []
        for (location_id, counting_id), jd_list in job_details_by_location.items():
            # Forcer tous les JobDetail non TERMINE de cette location à TERMINE
            for jd in jd_list:
                if jd.status != 'TERMINE':
                    if not dry_run:
                        jd.status = 'TERMINE'
                        jd.termine_date = now
                        job_details_to_update.append(jd)
                    result['job_details_forced_terminated'] += 1
                    location_ref = jd.location.location_reference if jd.location else "N/A"
                    self.stdout.write(
                        f'  🔄 JobDetail {jd.reference} forcé à TERMINE '
                        f'(emplacement: {location_ref})'
                    )
        
        # Bulk update des JobDetail
        if job_details_to_update and not dry_run:
            JobDetail.objects.bulk_update(job_details_to_update, ['status', 'termine_date'])
            self.stdout.write(
                self.style.SUCCESS(
                    f'  ✅ {len(job_details_to_update)} JobDetail(s) forcé(s) à TERMINE'
                )
            )
        
        # 3. Clôturer l'assignment
        if not dry_run:
            assignment.status = 'TERMINE'
            assignment.termine_date = now
            assignment.save()
        
        result['assignment_closed'] = 1
        total_job_details_all = job_details.count()
        job_details_en_attente_count = job_details.exclude(status='TERMINE').count()
        self.stdout.write(
            self.style.SUCCESS(
                f'  ✅ Assignment {assignment.reference} clôturé '
                f'({total_job_details} JobDetail(s) < 8, {job_details_en_attente_count} "EN ATTENTE", {total_job_details_all} total)'
            )
        )
        
        # 4. Synchroniser les CountingDetail entre les deux countings
        if not dry_run:
            sync_result = self._synchronize_counting_details_if_needed(job, assignment, force_sync=False)
            if sync_result.get('synchronized', False):
                created_count = sync_result.get('created_count', 0)
                result['counting_details_synced'] = 1
                result['counting_details_created'] = created_count
                sync_type = "forcée" if sync_result.get('forced', False) else "normale"
                self.stdout.write(
                    f'  🔄 {created_count} CountingDetail créé(s) lors de la synchronisation {sync_type} '
                    f'entre les countings {sync_result.get("counting_1_order")} et {sync_result.get("counting_2_order")}'
                )
        
        # 5. Vérifier si tous les assignments du job sont terminés
        all_assignments = Assigment.objects.filter(job=job)
        all_assignments_terminated = all_assignments.exclude(status='TERMINE').count() == 0
        
        # 6. Vérifier si tous les EcartComptage de l'inventaire ont un final_result non null
        ecart_comptages = EcartComptage.objects.filter(inventory=job.inventory)
        if ecart_comptages.exists():
            all_ecarts_have_final_result = ecart_comptages.filter(final_result__isnull=True).count() == 0
        else:
            all_ecarts_have_final_result = True
        
        # 7. Clôturer le job seulement si toutes les conditions sont remplies
        if all_assignments_terminated and all_ecarts_have_final_result:
            if job.status == 'TERMINE':
                result['job_already_terminated'] = 1
                self.stdout.write(
                    self.style.WARNING(
                        f'  ℹ️  Job {job.reference} déjà TERMINE'
                    )
                )
            else:
                if not dry_run:
                    job.status = 'TERMINE'
                    job.termine_date = now
                    job.save()
                result['job_closed'] = 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✅ Job {job.reference} clôturé '
                        f'(tous les assignments TERMINE et tous les écarts résolus)'
                    )
                )
        else:
            reasons = []
            if not all_assignments_terminated:
                non_terminated_count = all_assignments.exclude(status='TERMINE').count()
                reasons.append(f'{non_terminated_count} assignment(s) non terminé(s)')
            if not all_ecarts_have_final_result:
                ecarts_without_result = ecart_comptages.filter(final_result__isnull=True).count()
                reasons.append(f'{ecarts_without_result} écart(s) sans final_result')
            self.stdout.write(
                self.style.WARNING(
                    f'  ⚠️  Job {job.reference} non clôturé: {", ".join(reasons)}'
                )
            )
        
        return result
    
    def _synchronize_counting_details_if_needed(
        self, 
        job: Job, 
        assignment: Assigment,
        force_sync: bool = False
    ) -> dict:
        """
        Synchronise les CountingDetail entre les deux countings (order 1 et 2) si nécessaire.
        
        Args:
            job: Le job concerné
            assignment: L'assignment qui vient d'être clôturé
            force_sync: Si True, force la synchronisation même si l'autre assignment n'est pas TERMINE
            
        Returns:
            Dictionnaire avec les informations de synchronisation
        """
        counting_order = assignment.counting.order
        
        # Ne synchroniser que si counting_order est 1 ou 2
        if counting_order not in [1, 2]:
            return {
                'synchronized': False,
                'reason': f'Counting order {counting_order} ne nécessite pas de synchronisation'
            }
        
        # Déterminer l'autre counting_order
        other_counting_order = 2 if counting_order == 1 else 1
        
        # Récupérer l'assignment de l'autre counting pour ce job
        try:
            other_assignment = Assigment.objects.get(
                job=job,
                counting__order=other_counting_order
            )
        except Assigment.DoesNotExist:
            return {
                'synchronized': False,
                'reason': f'Assignment avec counting order {other_counting_order} non trouvé pour ce job'
            }
        
        # Vérifier si l'autre assignment est TERMINE (sauf si force_sync=True)
        if not force_sync and other_assignment.status != 'TERMINE':
            return {
                'synchronized': False,
                'reason': f'Assignment avec counting order {other_counting_order} n\'est pas encore TERMINE'
            }
        
        # Si force_sync=True et l'autre assignment n'est pas TERMINE, on synchronise quand même
        forced = force_sync and other_assignment.status != 'TERMINE'
        
        # Synchroniser (les deux assignments sont TERMINE, ou force_sync=True)
        counting_1 = assignment.counting if counting_order == 1 else other_assignment.counting
        counting_2 = other_assignment.counting if counting_order == 1 else assignment.counting
        
        if forced:
            self.stdout.write(
                self.style.WARNING(
                    f'  ⚠️  Synchronisation forcée : l\'assignment {other_assignment.reference} '
                    f'(counting {other_counting_order}) n\'est pas encore TERMINE'
                )
            )
        
        # Récupérer tous les CountingDetail des deux countings pour ce job
        counting_details_1 = CountingDetail.objects.filter(
            job=job,
            counting=counting_1
        ).select_related('location', 'product')
        
        counting_details_2 = CountingDetail.objects.filter(
            job=job,
            counting=counting_2
        ).select_related('location', 'product')
        
        # Créer des sets pour la comparaison rapide
        # Clé de comparaison : (location_id, product_id, dlc, n_lot)
        def get_comparison_key(cd: CountingDetail) -> Tuple[int, Optional[int], Optional[str], Optional[str]]:
            return (
                cd.location_id,
                cd.product_id if cd.product else None,
                cd.dlc.isoformat() if cd.dlc else None,
                cd.n_lot or None
            )
        
        # Créer des dictionnaires pour accès rapide
        details_1_dict = {get_comparison_key(cd): cd for cd in counting_details_1}
        details_2_dict = {get_comparison_key(cd): cd for cd in counting_details_2}
        
        # Trouver les lignes manquantes dans counting_2
        missing_in_2 = []
        for key, cd_1 in details_1_dict.items():
            if key not in details_2_dict:
                missing_in_2.append({
                    'location': cd_1.location,
                    'product': cd_1.product,
                    'dlc': cd_1.dlc,
                    'n_lot': cd_1.n_lot,
                    'counting': counting_2,
                    'job': job
                })
        
        # Trouver les lignes manquantes dans counting_1
        missing_in_1 = []
        for key, cd_2 in details_2_dict.items():
            if key not in details_1_dict:
                missing_in_1.append({
                    'location': cd_2.location,
                    'product': cd_2.product,
                    'dlc': cd_2.dlc,
                    'n_lot': cd_2.n_lot,
                    'counting': counting_1,
                    'job': job
                })
        
        # Créer les CountingDetail manquants avec quantité 0
        created_count = 0
        counting_details_to_create = []
        
        for item in missing_in_2:
            counting_detail = CountingDetail(
                quantity_inventoried=0,
                product=item['product'],
                dlc=item['dlc'],
                n_lot=item['n_lot'],
                location=item['location'],
                counting=item['counting'],
                job=item['job'],
                last_synced_at=timezone.now()
            )
            counting_detail.reference = counting_detail.generate_reference(CountingDetail.REFERENCE_PREFIX)
            counting_details_to_create.append(counting_detail)
            created_count += 1
        
        for item in missing_in_1:
            counting_detail = CountingDetail(
                quantity_inventoried=0,
                product=item['product'],
                dlc=item['dlc'],
                n_lot=item['n_lot'],
                location=item['location'],
                counting=item['counting'],
                job=item['job'],
                last_synced_at=timezone.now()
            )
            counting_detail.reference = counting_detail.generate_reference(CountingDetail.REFERENCE_PREFIX)
            counting_details_to_create.append(counting_detail)
            created_count += 1
        
        # Bulk create si nécessaire
        if counting_details_to_create:
            CountingDetail.objects.bulk_create(counting_details_to_create)
            
            # Régénérer les références avec les IDs réels
            for cd in counting_details_to_create:
                cd.reference = cd.generate_reference(CountingDetail.REFERENCE_PREFIX)
            CountingDetail.objects.bulk_update(counting_details_to_create, ['reference'])
        
        return {
            'synchronized': True,
            'created_count': created_count,
            'counting_1_order': counting_1.order,
            'counting_2_order': counting_2.order,
            'forced': forced
        }

