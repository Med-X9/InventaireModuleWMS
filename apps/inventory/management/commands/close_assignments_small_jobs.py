"""
Commande Django pour clôturer les assignments des comptages 1 et 2 pour les petits jobs.

Cette commande applique la même logique que CloseJobView avec des conditions supplémentaires :
- Récupère les assignments avec counting order 1 ou 2 qui ne sont pas TERMINE, regroupés par job
- Ne traite que les jobs qui ont exactement UN SEUL assignment non TERMINE (sur les countings 1 et 2)
- Vérifie que le total des JobDetail liés à l'assignment avec le job et le counting est ≤ 7
- Si > 7, ignore l'assignment et passe au suivant
- Si ≤ 7, FORCE tous les JobDetail à TERMINE
- Clôture l'assignment
- FORCE la synchronisation des CountingDetail entre les deux countings (même si l'autre assignment n'est pas TERMINE)
- Vérifie si tous les assignments du job sont TERMINE
- Vérifie si tous les EcartComptage de l'inventaire ont un final_result non null
- Clôture le job si toutes les conditions sont remplies

Exemple d'utilisation:
    python manage.py close_assignments_small_jobs --inventory-id 2 --warehouse-id 1
    python manage.py close_assignments_small_jobs --inventory-id 2 --warehouse-id 1 --dry-run
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
    help = 'Clôture les assignments des comptages 1 et 2 si tous les JobDetail liés sont TERMINE (max 7 JobDetail, un seul assignment non TERMINE par job)'

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
        
        self.stdout.write(self.style.SUCCESS('📋 Clôture des assignments des comptages 1 et 2 (jobs avec ≤ 7 JobDetail, un seul assignment non TERMINE)'))
        self.stdout.write(f'  🔍 Inventaire ID: {inventory_id}')
        self.stdout.write(f'  🔍 Entrepôt ID: {warehouse_id}')
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODE DRY-RUN : Aucune modification ne sera effectuée'))
        
        # Récupérer les assignments avec counting order 1 ou 2 qui ne sont pas TERMINE
        # Filtrer par inventory_id et warehouse_id
        # IMPORTANT: Ne traiter que les jobs qui ont exactement un seul assignment non TERMINE
        all_assignments = Assigment.objects.filter(
            counting__order__in=[1, 2],
            job__inventory_id=inventory_id,
            job__warehouse_id=warehouse_id
        ).select_related(
            'job',
            'job__inventory',
            'job__warehouse',
            'counting'
        )
        
        # Grouper par job et filtrer ceux qui ont exactement un seul assignment non TERMINE
        assignments_by_job = defaultdict(list)
        for assignment in all_assignments:
            assignments_by_job[assignment.job_id].append(assignment)
        
        # Filtrer pour ne garder que les jobs avec exactement un seul assignment non TERMINE
        assignments_to_process = []
        jobs_with_multiple_non_terminated = []
        
        for job_id, job_assignments in assignments_by_job.items():
            non_terminated = [a for a in job_assignments if a.status != 'TERMINE']
            if len(non_terminated) == 1:
                assignments_to_process.append(non_terminated[0])
            elif len(non_terminated) > 1:
                jobs_with_multiple_non_terminated.append(job_id)
        
        # Trier par counting.order, puis par job_id
        assignments_to_process.sort(key=lambda a: (a.counting.order, a.job_id))
        
        total_assignments = len(assignments_to_process)
        self.stdout.write(f'  ✅ {total_assignments} assignment(s) trouvé(s) (counting order 1 ou 2, un seul non TERMINE par job)')
        
        if jobs_with_multiple_non_terminated:
            self.stdout.write(
                self.style.WARNING(
                    f'  ⚠️  {len(jobs_with_multiple_non_terminated)} job(s) ignoré(s) '
                    f'(plusieurs assignments non TERMINE)'
                )
            )
        
        if total_assignments == 0:
            self.stdout.write(self.style.WARNING('⚠️  Aucun assignment à traiter'))
            return
        
        # Statistiques
        stats = {
            'total_assignments_found': total_assignments,
            'total_processed': 0,
            'assignments_closed': 0,
            'assignments_already_terminated': 0,
            'assignments_skipped_too_many_job_details': 0,
            'jobs_skipped_multiple_non_terminated': len(jobs_with_multiple_non_terminated),
            'jobs_closed': 0,
            'jobs_already_terminated': 0,
            'job_details_forced_terminated': 0,
            'counting_details_synced': 0,
            'counting_details_created': 0,
            'jobs_processed': set(),  # Set pour éviter les doublons
            'errors': []
        }
        
        if dry_run:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('SIMULATION - Ce qui sera fait:')
            self.stdout.write('='*60)
        
        # Traiter chaque assignment
        # Utiliser un dictionnaire pour suivre les jobs déjà traités (pour éviter de clôturer plusieurs fois)
        processed_jobs = set()
        
        for assignment in assignments_to_process:
            try:
                # Vérifier si l'assignment est déjà TERMINE (ne devrait pas arriver avec le filtre, mais sécurité)
                if assignment.status == 'TERMINE':
                    stats['assignments_already_terminated'] += 1
                    continue
                
                result = self.process_assignment(assignment, dry_run)
                stats['total_processed'] += 1
                stats['assignments_closed'] += result['assignment_closed']
                stats['jobs_closed'] += result['job_closed']
                stats['assignments_skipped_too_many_job_details'] += result.get('skipped_too_many_job_details', 0)
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
        self.stdout.write(f"  Assignments déjà TERMINE: {stats['assignments_already_terminated']}")
        self.stdout.write(f"  Jobs ignorés (plusieurs assignments non TERMINE): {stats['jobs_skipped_multiple_non_terminated']}")
        self.stdout.write(f"  Assignments ignorés (> 7 JobDetail): {stats['assignments_skipped_too_many_job_details']}")
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
        Traite un assignment en appliquant la même logique que CloseJobView avec condition supplémentaire :
        0. Vérifie que le total des JobDetail avec statut "EN ATTENTE" (non TERMINE) est ≤ 7
        1. Si ≤ 7, FORCE tous les JobDetail non TERMINE du job liés au même counting à TERMINE
        2. Clôture l'assignment
        3. Synchronise les CountingDetail entre les deux countings (forcé pour jobs ≤ 7 JobDetail EN ATTENTE)
        4. Vérifie si tous les assignments du job sont TERMINE
        5. Vérifie si tous les EcartComptage de l'inventaire ont un final_result non null
        6. Si les deux conditions précédentes sont remplies, clôture le job
        
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
        
        # 0. Vérifier que le total des JobDetail avec statut "EN ATTENTE" (non TERMINE) est ≤ 7
        job_details_all = JobDetail.objects.filter(
            job=job,
            counting=counting
        ).select_related('location')
        
        # Compter uniquement les JobDetail qui ne sont pas TERMINE (statut "EN ATTENTE")
        job_details_en_attente = job_details_all.exclude(status='TERMINE')
        total_job_details_en_attente = job_details_en_attente.count()
        total_job_details_all = job_details_all.count()
        
        # Condition supplémentaire : total des JobDetail "EN ATTENTE" doit être ≤ 7
        if total_job_details_en_attente > 7:
            result['skipped_too_many_job_details'] = 1
            self.stdout.write(
                self.style.WARNING(
                    f'  ⚠️  Assignment {assignment.reference} ignoré : '
                    f'{total_job_details_en_attente} JobDetail(s) "EN ATTENTE" trouvé(s) '
                    f'(sur {total_job_details_all} total, limite: 7) '
                    f'pour le counting {counting_order}'
                )
            )
            return result
        
        # Utiliser tous les JobDetail pour le traitement (y compris ceux déjà TERMINE)
        job_details = job_details_all
        
        # 1. Si ≤ 7, FORCER tous les JobDetail à TERMINE
        # IMPORTANT: Gérer les doublons (même job, même location, même counting)
        # Pour chaque combinaison unique (location, counting), forcer au moins un JobDetail à TERMINE
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
        
        # 2. Clôturer l'assignment
        if not dry_run:
            assignment.status = 'TERMINE'
            assignment.termine_date = now
            assignment.save()
        
        result['assignment_closed'] = 1
        self.stdout.write(
            self.style.SUCCESS(
                f'  ✅ Assignment {assignment.reference} clôturé '
                f'({total_job_details_en_attente} JobDetail(s) "EN ATTENTE" ≤ 7, {total_job_details_all} total)'
            )
        )
        
        # 3. Synchroniser les CountingDetail entre les deux countings si nécessaire
        # FORCER la synchronisation pour les jobs avec ≤ 7 JobDetail
        if not dry_run:
            sync_result = self._synchronize_counting_details_if_needed(job, assignment, force_sync=True)
            if sync_result.get('synchronized', False):
                created_count = sync_result.get('created_count', 0)
                result['counting_details_synced'] = 1  # Une synchronisation effectuée
                result['counting_details_created'] = created_count  # Nombre de lignes créées
                sync_type = "forcée" if sync_result.get('forced', False) else "normale"
                self.stdout.write(
                    f'  🔄 {created_count} CountingDetail créé(s) lors de la synchronisation {sync_type} '
                    f'entre les countings {sync_result.get("counting_1_order")} et {sync_result.get("counting_2_order")}'
                )
        
        # 4. Vérifier si tous les assignments du job sont terminés
        all_assignments = Assigment.objects.filter(job=job)
        all_assignments_terminated = all_assignments.exclude(status='TERMINE').count() == 0
        
        # 5. Vérifier si tous les EcartComptage de l'inventaire ont un final_result non null
        ecart_comptages = EcartComptage.objects.filter(inventory=job.inventory)
        if ecart_comptages.exists():
            all_ecarts_have_final_result = ecart_comptages.filter(final_result__isnull=True).count() == 0
        else:
            all_ecarts_have_final_result = True
        
        # 6. Clôturer le job seulement si toutes les conditions sont remplies
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
        Si force_sync=True, force la synchronisation même si l'autre assignment n'est pas TERMINE.
        
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

