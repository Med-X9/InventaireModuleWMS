"""
Commande Django pour forcer la clôture de jobs avec création de CountingDetail à 0.

Cette commande :
- Force tous les JobDetail à TERMINE
- Vérifie/crée les countings si nécessaire
- Crée des CountingDetail avec quantité 0 pour tous les JobDetail
- Change le statut des assignments à TERMINE
- Clôture le job

Exemple d'utilisation:
    python manage.py force_close_jobs_with_zero_counting_details --job-refs JOB-0585 JOB-0558
    python manage.py force_close_jobs_with_zero_counting_details --file jobs_list.txt
    python manage.py force_close_jobs_with_zero_counting_details --dry-run
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from collections import defaultdict
from typing import Optional, List, Tuple, Dict, Any
import logging

from apps.inventory.models import Job, Assigment, JobDetail, CountingDetail, EcartComptage, Counting, Inventory
from apps.masterdata.models import Product

logger = logging.getLogger(__name__)

# Liste statique des références de jobs
STATIC_JOB_REFERENCES = [
    'JOB-0585',
    'JOB-0558',
]


class Command(BaseCommand):
    help = 'Force la clôture de jobs avec création de CountingDetail à 0'

    def add_arguments(self, parser):
        parser.add_argument(
            '--job-refs',
            nargs='+',
            type=str,
            help='Liste des références de jobs à clôturer (ex: JOB-0585 JOB-0558)',
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Chemin vers un fichier texte contenant les références de jobs (une par ligne)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : affiche ce qui sera fait sans modifier la base de données',
        )

    def handle(self, *args, **options):
        job_refs = options.get('job_refs', [])
        file_path = options.get('file')
        dry_run = options.get('dry_run', False)
        
        # Récupérer les références depuis le fichier si fourni
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_refs = [line.strip() for line in f if line.strip()]
                    job_refs.extend(file_refs)
            except FileNotFoundError:
                raise CommandError(f"Fichier non trouvé: {file_path}")
            except Exception as e:
                raise CommandError(f"Erreur lors de la lecture du fichier: {str(e)}")
        
        # Si aucune référence n'a été fournie, utiliser la liste statique par défaut
        if not job_refs:
            job_refs = STATIC_JOB_REFERENCES.copy()
            self.stdout.write(self.style.SUCCESS(f'📋 Utilisation de la liste statique par défaut: {len(job_refs)} job(s)'))
        
        if not job_refs:
            raise CommandError(
                "Aucune référence de job trouvée. Utilisez --job-refs ou --file"
            )
        
        # Supprimer les doublons
        job_refs = list(set(job_refs))
        
        self.stdout.write(self.style.SUCCESS(f'📋 Clôture forcée de {len(job_refs)} job(s)'))
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODE DRY-RUN : Aucune modification ne sera effectuée'))
        
        # Récupérer les jobs par leurs références
        jobs = Job.objects.filter(reference__in=job_refs).select_related('inventory', 'warehouse')
        
        found_refs = set(jobs.values_list('reference', flat=True))
        missing_refs = set(job_refs) - found_refs
        
        if missing_refs:
            self.stdout.write(self.style.ERROR(
                f'❌ Jobs non trouvés: {", ".join(sorted(missing_refs))}'
            ))
        
        if not jobs.exists():
            self.stdout.write(self.style.ERROR('❌ Aucun job trouvé'))
            return
        
        self.stdout.write(f'  ✅ Jobs trouvés: {jobs.count()}')
        
        # Statistiques
        stats = {
            'jobs_processed': 0,
            'jobs_closed': 0,
            'assignments_closed': 0,
            'job_details_closed': 0,
            'countings_created': 0,
            'counting_details_created': 0,
            'errors': []
        }
        
        if dry_run:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('SIMULATION - Ce qui sera fait:')
            self.stdout.write('='*60)
        
        # Traiter chaque job
        for job in jobs:
            try:
                result = self.process_job(job, dry_run)
                stats['jobs_processed'] += 1
                stats['jobs_closed'] += result['job_closed']
                stats['assignments_closed'] += result['assignments_closed']
                stats['job_details_closed'] += result['job_details_closed']
                stats['countings_created'] += result['countings_created']
                stats['counting_details_created'] += result['counting_details_created']
            except Exception as e:
                error_msg = f"Erreur lors du traitement du job {job.reference}: {str(e)}"
                stats['errors'].append(error_msg)
                self.stdout.write(self.style.ERROR(f'  ❌ {error_msg}'))
                logger.error(error_msg, exc_info=True)
        
        # Afficher le résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 RÉSUMÉ'))
        self.stdout.write('='*60)
        self.stdout.write(f"  Jobs traités: {stats['jobs_processed']}")
        self.stdout.write(f"  Jobs clôturés: {stats['jobs_closed']}")
        self.stdout.write(f"  Assignments clôturés: {stats['assignments_closed']}")
        self.stdout.write(f"  JobDetails forcés à TERMINE: {stats['job_details_closed']}")
        self.stdout.write(f"  Countings créés: {stats['countings_created']}")
        self.stdout.write(f"  CountingDetails créés: {stats['counting_details_created']}")
        
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f"\n  ❌ Erreurs: {len(stats['errors'])}"))
            for error in stats['errors']:
                self.stdout.write(self.style.ERROR(f"    - {error}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  MODE DRY-RUN : Aucune modification n\'a été effectuée'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Traitement terminé avec succès!'))
    
    def _get_or_create_default_product(self, dry_run: bool) -> Optional[Product]:
        """
        Récupère ou crée le produit avec codebarre 1111111111111.
        
        Args:
            dry_run: Si True, ne crée pas réellement
            
        Returns:
            Product object ou None
        """
        barcode = '1111111111111'
        try:
            product = Product.objects.get(Barcode=barcode)
            return product
        except Product.DoesNotExist:
            if not dry_run:
                # Créer le produit avec codebarre 1111111111111
                # Il faut une famille de produit, on prend la première disponible
                from apps.masterdata.models import Family
                family = Family.objects.first()
                if not family:
                    self.stdout.write(
                        self.style.ERROR(
                            '  ❌ Aucune famille de produit trouvée, impossible de créer le produit par défaut'
                        )
                    )
                    return None
                
                product = Product(
                    Internal_Product_Code='DEFAULT-1111111111111',
                    Short_Description='Produit par défaut',
                    Barcode=barcode,
                    Stock_Unit='PIECE',
                    Product_Status='ACTIVE',
                    Product_Family=family,
                    Is_Variant=False,
                    n_lot=False,
                    n_serie=False,
                    dlc=False
                )
                product.reference = product.generate_reference(Product.CODE_PREFIX)
                product.save()
                self.stdout.write(f'  ✅ Produit par défaut créé: {product.reference} (codebarre: {barcode})')
                return product
            else:
                self.stdout.write(f'  [DRY-RUN] Produit par défaut avec codebarre {barcode} serait créé')
                return None
        except Product.MultipleObjectsReturned:
            product = Product.objects.filter(Barcode=barcode).first()
            return product
    
    def _get_or_create_counting(self, inventory: Inventory, order: int, dry_run: bool) -> Optional[Counting]:
        """
        Récupère ou crée un counting avec l'ordre spécifié.
        
        Args:
            inventory: L'inventaire
            order: L'ordre du counting
            dry_run: Si True, ne crée pas réellement
            
        Returns:
            Counting object ou None
        """
        try:
            counting = Counting.objects.get(inventory=inventory, order=order)
            return counting
        except Counting.DoesNotExist:
            # Créer le counting avec des valeurs par défaut
            if not dry_run:
                counting = Counting(
                    inventory=inventory,
                    order=order,
                    count_mode='GENERAL',
                    unit_scanned=False,
                    entry_quantity=False,
                    is_variant=False,
                    n_lot=False,
                    n_serie=False,
                    dlc=False,
                    show_product=False,
                    stock_situation=False,
                    quantity_show=False
                )
                counting.reference = counting.generate_reference(Counting.REFERENCE_PREFIX)
                counting.save()
                self.stdout.write(f'  ✅ Counting order {order} créé: {counting.reference}')
                return counting
            else:
                self.stdout.write(f'  [DRY-RUN] Counting order {order} serait créé')
                return None
        except Counting.MultipleObjectsReturned:
            counting = Counting.objects.filter(inventory=inventory, order=order).first()
            return counting
    
    @transaction.atomic
    def process_job(self, job: Job, dry_run: bool = False) -> dict:
        """
        Traite un job en forçant toutes les mises à jour :
        1. Force tous les JobDetail à TERMINE
        2. Vérifie/crée les countings si nécessaire
        3. Crée des CountingDetail avec quantité 0 pour tous les JobDetail
        4. Change le statut des assignments à TERMINE
        5. Clôture le job
        
        Args:
            job: Le job à traiter
            dry_run: Si True, ne fait que simuler les actions
            
        Returns:
            Dictionnaire avec les statistiques du traitement
        """
        result = {
            'job_closed': 0,
            'assignments_closed': 0,
            'job_details_closed': 0,
            'countings_created': 0,
            'counting_details_created': 0
        }
        
        self.stdout.write(f'\n📦 Job: {job.reference} (ID: {job.id})')
        
        # 1. Forcer TOUS les JobDetail à TERMINE (même ceux déjà TERMINE pour mettre à jour la date)
        all_job_details = JobDetail.objects.filter(job=job).select_related('location', 'counting')
        now = timezone.now()
        job_details_to_update = []
        
        for jd in all_job_details:
            # Vérifier le statut avant modification
            was_terminated = (jd.status == 'TERMINE')
            
            # Forcer le statut à TERMINE et mettre à jour la date pour TOUS les JobDetail
            if not dry_run:
                jd.status = 'TERMINE'
                jd.termine_date = now
                job_details_to_update.append(jd)
            
            if not was_terminated:
                result['job_details_closed'] += 1
                self.stdout.write(f'  ✅ JobDetail {jd.reference} → TERMINE (statut changé)')
            else:
                self.stdout.write(f'  ✅ JobDetail {jd.reference} → TERMINE (déjà TERMINE, date mise à jour)')
        
        if job_details_to_update and not dry_run:
            JobDetail.objects.bulk_update(job_details_to_update, ['status', 'termine_date'])
            self.stdout.write(f'  ✅ {len(job_details_to_update)} JobDetail(s) mis à jour')
        
        # 2. Vérifier/créer les countings si nécessaire
        # Récupérer tous les countings uniques utilisés par les JobDetail
        counting_orders = set(all_job_details.values_list('counting__order', flat=True).distinct())
        counting_orders = {o for o in counting_orders if o is not None}
        
        # Si aucun counting n'est trouvé, créer un counting order 1 par défaut
        if not counting_orders:
            counting_orders = {1}
            self.stdout.write(f'  ⚠️  Aucun counting trouvé, création d\'un counting order 1 par défaut')
        
        countings = {}
        for order in counting_orders:
            counting = self._get_or_create_counting(job.inventory, order, dry_run)
            if counting:
                countings[order] = counting
                if counting.id is None:  # Nouvellement créé
                    result['countings_created'] += 1
        
        # 3. Mapper les CountingDetail entre counting order 1 et 2
        # Récupérer ou créer le produit avec codebarre 1111111111111
        default_product = self._get_or_create_default_product(dry_run)
        
        # Vérifier que les countings order 1 et 2 existent
        counting_1 = countings.get(1)
        counting_2 = countings.get(2)
        
        if not counting_1:
            counting_1 = self._get_or_create_counting(job.inventory, 1, dry_run)
            if counting_1:
                countings[1] = counting_1
                if counting_1.id is None:
                    result['countings_created'] += 1
        
        if not counting_2:
            counting_2 = self._get_or_create_counting(job.inventory, 2, dry_run)
            if counting_2:
                countings[2] = counting_2
                if counting_2.id is None:
                    result['countings_created'] += 1
        
        if counting_1 and counting_2:
            # Mapper les CountingDetail entre counting 1 et 2
            counting_details_to_create = self._map_counting_details_between_countings(
                job, counting_1, counting_2, default_product, now, dry_run
            )
            result['counting_details_created'] += len(counting_details_to_create)
            
            if counting_details_to_create and not dry_run:
                CountingDetail.objects.bulk_create(counting_details_to_create)
                # Régénérer les références avec les IDs réels
                for cd in counting_details_to_create:
                    cd.reference = cd.generate_reference(CountingDetail.REFERENCE_PREFIX)
                CountingDetail.objects.bulk_update(counting_details_to_create, ['reference'])
                self.stdout.write(f'  ✅ {len(counting_details_to_create)} CountingDetail(s) créé(s) lors du mapping')
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'  ⚠️  Impossible de mapper : counting 1 ou 2 manquant'
                )
            )
        
        # 4. Clôturer les Assignments
        assignments = Assigment.objects.filter(job=job).select_related('counting')
        
        for assignment in assignments:
            if assignment.status != 'TERMINE':
                if not dry_run:
                    assignment.status = 'TERMINE'
                    assignment.termine_date = now
                    assignment.save()
                result['assignments_closed'] += 1
                self.stdout.write(f'  ✅ Assignment {assignment.reference} → TERMINE')
        
        # 5. Clôturer le job
        if job.status != 'TERMINE':
            if not dry_run:
                job.status = 'TERMINE'
                job.termine_date = now
                job.save()
            result['job_closed'] = 1
            self.stdout.write(f'  ✅ Job {job.reference} → TERMINE')
        
        return result
    
    def _map_counting_details_between_countings(
        self,
        job: Job,
        counting_1: Counting,
        counting_2: Counting,
        default_product: Optional[Product],
        now,
        dry_run: bool
    ) -> List[CountingDetail]:
        """
        Mappe les CountingDetail entre counting order 1 et 2.
        Si un CountingDetail existe dans un counting mais pas dans l'autre (même emplacement + article),
        crée le manquant avec produit codebarre 1111111111111 et quantité 0.
        
        Args:
            job: Le job
            counting_1: Counting order 1
            counting_2: Counting order 2
            default_product: Produit par défaut avec codebarre 1111111111111
            now: Date actuelle
            dry_run: Si True, ne crée pas réellement
            
        Returns:
            Liste des CountingDetail à créer
        """
        counting_details_to_create = []
        
        # Récupérer tous les CountingDetail des deux countings
        counting_details_1 = CountingDetail.objects.filter(
            job=job,
            counting=counting_1
        ).select_related('location', 'product')
        
        counting_details_2 = CountingDetail.objects.filter(
            job=job,
            counting=counting_2
        ).select_related('location', 'product')
        
        # Créer des clés de comparaison : (location_id, product_id, dlc, n_lot)
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
        
        # Trouver les CountingDetail manquants dans counting_2
        for key, cd_1 in details_1_dict.items():
            if key not in details_2_dict:
                # Créer le CountingDetail manquant dans counting_2
                # Utiliser le produit du cd_1, ou le produit par défaut si pas de produit
                product_to_use = cd_1.product if cd_1.product else default_product
                
                if not product_to_use:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  Pas de produit disponible pour créer CountingDetail manquant '
                            f'(location: {cd_1.location.location_reference if cd_1.location else "N/A"})'
                        )
                    )
                    continue
                
                counting_detail = CountingDetail(
                    quantity_inventoried=0,
                    product=product_to_use,
                    dlc=cd_1.dlc,
                    n_lot=cd_1.n_lot,
                    location=cd_1.location,
                    counting=counting_2,
                    job=job,
                    last_synced_at=now
                )
                counting_detail.reference = counting_detail.generate_reference(CountingDetail.REFERENCE_PREFIX)
                counting_details_to_create.append(counting_detail)
                self.stdout.write(
                    f'  ✅ CountingDetail à créer dans counting 2: location={cd_1.location.location_reference if cd_1.location else "N/A"}, '
                    f'product={product_to_use.Internal_Product_Code if product_to_use else "N/A"}, quantité=0'
                )
        
        # Trouver les CountingDetail manquants dans counting_1
        for key, cd_2 in details_2_dict.items():
            if key not in details_1_dict:
                # Créer le CountingDetail manquant dans counting_1
                # Utiliser le produit du cd_2, ou le produit par défaut si pas de produit
                product_to_use = cd_2.product if cd_2.product else default_product
                
                if not product_to_use:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  Pas de produit disponible pour créer CountingDetail manquant '
                            f'(location: {cd_2.location.location_reference if cd_2.location else "N/A"})'
                        )
                    )
                    continue
                
                counting_detail = CountingDetail(
                    quantity_inventoried=0,
                    product=product_to_use,
                    dlc=cd_2.dlc,
                    n_lot=cd_2.n_lot,
                    location=cd_2.location,
                    counting=counting_1,
                    job=job,
                    last_synced_at=now
                )
                counting_detail.reference = counting_detail.generate_reference(CountingDetail.REFERENCE_PREFIX)
                counting_details_to_create.append(counting_detail)
                self.stdout.write(
                    f'  ✅ CountingDetail à créer dans counting 1: location={cd_2.location.location_reference if cd_2.location else "N/A"}, '
                    f'product={product_to_use.Internal_Product_Code if product_to_use else "N/A"}, quantité=0'
                )
        
        return counting_details_to_create

