"""
Commande Django pour affecter des jobs aux comptages 1 et 2 depuis un fichier Excel.
Les usernames sont convertis en lowercase avant la recherche.

Format Excel attendu:
- job_reference: Référence du job (ex: JOB-0001) ou job_id: ID du job
- COMPTAGE 1: Username de la session pour le comptage 1 (ex: EQUIPE-21)
- COMPTAGE 2: Username de la session pour le comptage 2 (ex: EQUIPE-22)

Note: Les usernames sont automatiquement convertis en lowercase.

Exemple d'utilisation:
    python manage.py assign_jobs_from_excel --file data/assignments.xlsx --inventory-id 2 --warehouse-id 1
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
import logging

from apps.inventory.models import Job, Counting, Assigment
from apps.users.models import UserApp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Affecte des jobs aux comptages 1 et 2 depuis un fichier Excel (usernames en lowercase)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Chemin vers le fichier Excel (.xlsx)',
        )
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
            help='Mode test : affiche ce qui sera créé sans créer réellement',
        )
        parser.add_argument(
            '--sheet',
            type=str,
            default=0,
            help='Nom ou index de la feuille Excel à lire (défaut: première feuille)',
        )

    def read_excel_file(self, file_path, sheet_name_or_index=0):
        """
        Lit le fichier Excel et retourne les données.
        
        Args:
            file_path: Chemin vers le fichier Excel
            sheet_name_or_index: Nom ou index de la feuille
            
        Returns:
            Liste de dictionnaires avec les données
        """
        try:
            import openpyxl
        except ImportError:
            raise CommandError(
                "openpyxl n'est pas installé. Installez-le avec: pip install openpyxl"
            )
        
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
            
            # Obtenir la feuille
            if isinstance(sheet_name_or_index, int):
                sheet = wb.worksheets[sheet_name_or_index]
            else:
                sheet = wb[sheet_name_or_index]
            
            # Lire les en-têtes (première ligne)
            headers = []
            for cell in sheet[1]:
                headers.append(cell.value.strip() if cell.value else '')
            
            # Lire les données
            data = []
            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=False), start=2):
                row_data = {}
                for col_idx, cell in enumerate(row):
                    if col_idx < len(headers) and headers[col_idx]:
                        value = cell.value
                        # Convertir les valeurs en string si nécessaire
                        if value is not None:
                            if isinstance(value, (int, float)):
                                # Garder les nombres comme nombres
                                row_data[headers[col_idx]] = int(value) if isinstance(value, float) and value.is_integer() else value
                            else:
                                row_data[headers[col_idx]] = str(value).strip()
                        else:
                            row_data[headers[col_idx]] = None
                
                # Ignorer les lignes vides
                if any(row_data.values()):
                    data.append(row_data)
            
            wb.close()
            return data, headers
            
        except FileNotFoundError:
            raise CommandError(f"Fichier non trouvé: {file_path}")
        except Exception as e:
            raise CommandError(f"Erreur lors de la lecture du fichier Excel: {str(e)}")

    def get_job(self, job_identifier, inventory_id, warehouse_id):
        """
        Récupère un job par référence ou ID.
        
        Args:
            job_identifier: Référence du job (ex: JOB-0001) ou ID
            inventory_id: ID de l'inventaire pour validation
            warehouse_id: ID de l'entrepôt pour validation
            
        Returns:
            Job object
        """
        # Essayer d'abord comme ID (entier)
        try:
            job_id = int(job_identifier)
            try:
                job = Job.objects.get(id=job_id, inventory_id=inventory_id, warehouse_id=warehouse_id)
                return job
            except Job.DoesNotExist:
                raise CommandError(
                    f"Job avec l'ID {job_id} non trouvé pour l'inventaire {inventory_id} et warehouse {warehouse_id}"
                )
        except (ValueError, TypeError):
            # Si ce n'est pas un entier, traiter comme référence
            try:
                job = Job.objects.get(
                    reference=str(job_identifier),
                    inventory_id=inventory_id,
                    warehouse_id=warehouse_id
                )
                return job
            except Job.DoesNotExist:
                raise CommandError(
                    f"Job avec la référence '{job_identifier}' non trouvé pour l'inventaire {inventory_id} et warehouse {warehouse_id}"
                )
            except Job.MultipleObjectsReturned:
                raise CommandError(
                    f"Plusieurs jobs trouvés avec la référence '{job_identifier}' pour l'inventaire {inventory_id} et warehouse {warehouse_id}"
                )

    def get_session_by_username(self, username):
        """
        Récupère une session (UserApp de type Mobile) par username (en lowercase).
        
        Args:
            username: Username de la session (sera converti en lowercase)
            
        Returns:
            UserApp object ou None
        """
        if not username:
            return None
        
        # Convertir en lowercase
        username_lower = str(username).strip().lower()
        
        try:
            session = UserApp.objects.get(username__iexact=username_lower, type='Mobile', is_active=True)
            return session
        except UserApp.DoesNotExist:
            raise CommandError(
                f"Session avec le username '{username}' (recherché en lowercase: '{username_lower}') non trouvée (type Mobile)"
            )
        except UserApp.MultipleObjectsReturned:
            # Si plusieurs sessions trouvées, prendre la première
            session = UserApp.objects.filter(username__iexact=username_lower, type='Mobile', is_active=True).first()
            self.stdout.write(
                self.style.WARNING(
                    f"  ⚠ Plusieurs sessions trouvées pour '{username_lower}', utilisation de la première: {session.username}"
                )
            )
            return session

    def assign_job_to_countings(
        self,
        job,
        counting_1,
        counting_2,
        session_1=None,
        session_2=None,
        dry_run=False
    ):
        """
        Affecte un job aux comptages 1 et 2 avec des sessions spécifiques.
        Crée des assignments avec statut PRET.
        
        Args:
            job: Job object
            counting_1: Counting object pour le comptage 1
            counting_2: Counting object pour le comptage 2
            session_1: Session pour le comptage 1
            session_2: Session pour le comptage 2
            dry_run: Mode test
            
        Returns:
            Dict avec les statistiques de création
        """
        if dry_run:
            return {
                'assignments_created_1': 1 if session_1 else 0,
                'assignments_created_2': 1 if session_2 else 0,
                'assignments_updated_1': 0,
                'assignments_updated_2': 0
            }
        
        assignments_created_1 = 0
        assignments_created_2 = 0
        assignments_updated_1 = 0
        assignments_updated_2 = 0
        current_time = timezone.now()
        
        # Assignment pour le comptage 1
        if session_1:
            assignment_1, created_1 = Assigment.objects.get_or_create(
                job=job,
                counting=counting_1,
                defaults={
                    'reference': Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                    'session': session_1,
                    'status': 'PRET',
                    'pret_date': current_time,
                    'affecte_date': current_time,
                    'date_start': current_time
                }
            )
            
            if not created_1:
                # Mettre à jour l'assignment existant
                assignment_1.session = session_1
                assignment_1.status = 'PRET'
                assignment_1.pret_date = current_time
                assignment_1.affecte_date = current_time
                assignment_1.date_start = current_time
                assignment_1.save()
                assignments_updated_1 = 1
            else:
                assignments_created_1 = 1
        
        # Assignment pour le comptage 2
        if session_2:
            assignment_2, created_2 = Assigment.objects.get_or_create(
                job=job,
                counting=counting_2,
                defaults={
                    'reference': Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                    'session': session_2,
                    'status': 'PRET',
                    'pret_date': current_time,
                    'affecte_date': current_time,
                    'date_start': current_time
                }
            )
            
            if not created_2:
                # Mettre à jour l'assignment existant
                assignment_2.session = session_2
                assignment_2.status = 'PRET'
                assignment_2.pret_date = current_time
                assignment_2.affecte_date = current_time
                assignment_2.date_start = current_time
                assignment_2.save()
                assignments_updated_2 = 1
            else:
                assignments_created_2 = 1
        
        return {
            'assignments_created_1': assignments_created_1,
            'assignments_created_2': assignments_created_2,
            'assignments_updated_1': assignments_updated_1,
            'assignments_updated_2': assignments_updated_2
        }

    def handle(self, *args, **options):
        file_path = options['file']
        inventory_id = options['inventory_id']
        warehouse_id = options['warehouse_id']
        dry_run = options['dry_run']
        sheet = options['sheet']
        
        self.stdout.write(self.style.SUCCESS(f'📖 Lecture du fichier Excel: {file_path}'))
        self.stdout.write(f'  📦 Inventaire ID: {inventory_id}')
        self.stdout.write(f'  🏭 Warehouse ID: {warehouse_id}')
        
        # Valider que l'inventaire et le warehouse existent
        try:
            from apps.inventory.models import Inventory
            from apps.masterdata.models import Warehouse
            
            inventory = Inventory.objects.get(id=inventory_id)
            warehouse = Warehouse.objects.get(id=warehouse_id)
            
            self.stdout.write(f'  ✓ Inventaire: {inventory.reference} - {inventory.label}')
            self.stdout.write(f'  ✓ Warehouse: {warehouse.reference} - {warehouse.warehouse_name}')
        except Inventory.DoesNotExist:
            raise CommandError(f"Inventaire avec l'ID {inventory_id} non trouvé")
        except Warehouse.DoesNotExist:
            raise CommandError(f"Entrepôt avec l'ID {warehouse_id} non trouvé")
        
        # Récupérer les comptages 1 et 2
        counting_1 = Counting.objects.filter(inventory_id=inventory_id, order=1).first()
        counting_2 = Counting.objects.filter(inventory_id=inventory_id, order=2).first()
        
        if not counting_1:
            raise CommandError(f"Comptage d'ordre 1 non trouvé pour l'inventaire {inventory_id}")
        
        if not counting_2:
            raise CommandError(f"Comptage d'ordre 2 non trouvé pour l'inventaire {inventory_id}")
        
        self.stdout.write(f'  ✓ Comptage 1: {counting_1.reference}')
        self.stdout.write(f'  ✓ Comptage 2: {counting_2.reference}')
        
        # Lire le fichier Excel
        try:
            data, headers = self.read_excel_file(file_path, sheet)
            self.stdout.write(self.style.SUCCESS(f'\n✓ {len(data)} lignes lues'))
            self.stdout.write(f'  Colonnes détectées: {", ".join(headers)}')
        except Exception as e:
            raise CommandError(str(e))
        
        # Vérifier les colonnes requises
        required_columns = []
        job_column = None
        session_1_column = None
        session_2_column = None
        
        # Chercher la colonne job (job_reference ou job_id)
        for col in ['job_reference', 'job_id', 'reference', 'job']:
            if col in headers:
                job_column = col
                break
        
        if not job_column:
            raise CommandError(
                "Colonne job non trouvée. Utilisez 'job_reference', 'job_id', 'reference' ou 'job'"
            )
        
        # Chercher les colonnes de sessions
        for col in ['COMPTAGE 1', 'comptage 1', 'COMPTAGE1', 'comptage1', 'counting_1', 'session_1', 'session_id_1']:
            if col in headers:
                session_1_column = col
                break
        
        for col in ['COMPTAGE 2', 'comptage 2', 'COMPTAGE2', 'comptage2', 'counting_2', 'session_2', 'session_id_2']:
            if col in headers:
                session_2_column = col
                break
        
        if not session_1_column and not session_2_column:
            raise CommandError(
                "Aucune colonne de session trouvée. Utilisez 'COMPTAGE 1' et/ou 'COMPTAGE 2'"
            )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 MODE TEST - Aucune donnée ne sera créée\n'))
        
        # Traiter les affectations
        jobs_processed = 0
        assignments_created_1 = 0
        assignments_created_2 = 0
        assignments_updated_1 = 0
        assignments_updated_2 = 0
        errors = []
        
        self.stdout.write(self.style.SUCCESS('\n🏭 Affectation des jobs...\n'))
        
        for idx, row in enumerate(data, start=2):
            try:
                # Récupérer le job
                job_identifier = row.get(job_column)
                if not job_identifier:
                    errors.append(f"Ligne {idx}: {job_column} manquant")
                    continue
                
                job = self.get_job(job_identifier, inventory_id, warehouse_id)
                
                # Récupérer les sessions (convertir en lowercase)
                session_1 = None
                session_2 = None
                
                if session_1_column and row.get(session_1_column):
                    username_1 = str(row[session_1_column]).strip()
                    if username_1:
                        try:
                            session_1 = self.get_session_by_username(username_1)
                            self.stdout.write(
                                f"  👤 Job {job.reference} - Comptage 1: {session_1.username} ({session_1.nom} {session_1.prenom})"
                            )
                        except CommandError as e:
                            errors.append(f"Ligne {idx}: {str(e)}")
                            continue
                
                if session_2_column and row.get(session_2_column):
                    username_2 = str(row[session_2_column]).strip()
                    if username_2:
                        try:
                            session_2 = self.get_session_by_username(username_2)
                            self.stdout.write(
                                f"  👤 Job {job.reference} - Comptage 2: {session_2.username} ({session_2.nom} {session_2.prenom})"
                            )
                        except CommandError as e:
                            errors.append(f"Ligne {idx}: {str(e)}")
                            continue
                
                if not session_1 and not session_2:
                    errors.append(f"Ligne {idx}: Aucune session fournie pour le job {job.reference}")
                    continue
                
                # Affecter le job
                with transaction.atomic():
                    result = self.assign_job_to_countings(
                        job=job,
                        counting_1=counting_1,
                        counting_2=counting_2,
                        session_1=session_1,
                        session_2=session_2,
                        dry_run=dry_run
                    )
                    
                    if not dry_run:
                        jobs_processed += 1
                        assignments_created_1 += result['assignments_created_1']
                        assignments_created_2 += result['assignments_created_2']
                        assignments_updated_1 += result['assignments_updated_1']
                        assignments_updated_2 += result['assignments_updated_2']
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ Job {job.reference} affecté"
                            )
                        )
                    else:
                        jobs_processed += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"  [SIMULATION] Job {job.reference} serait affecté"
                            )
                        )
                        
            except Exception as e:
                error_msg = f"Ligne {idx}: Erreur - {str(e)}"
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(f"  ❌ {error_msg}"))
                if not dry_run:
                    continue
        
        # Afficher les erreurs
        if errors:
            self.stdout.write(self.style.ERROR('\n❌ Erreurs rencontrées:'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  • {error}"))
        
        # Résumé
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODE TEST - Résumé de simulation:'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Résumé de l\'affectation:'))
        
        self.stdout.write(f"  • Jobs traités: {jobs_processed}")
        self.stdout.write(f"  • Assignments créés (comptage 1): {assignments_created_1}")
        self.stdout.write(f"  • Assignments mis à jour (comptage 1): {assignments_updated_1}")
        self.stdout.write(f"  • Assignments créés (comptage 2): {assignments_created_2}")
        self.stdout.write(f"  • Assignments mis à jour (comptage 2): {assignments_updated_2}")
        self.stdout.write(f"  • Erreurs: {len(errors)}")
        self.stdout.write(self.style.SUCCESS('='*60))
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n💡 Pour créer réellement les assignments, relancez la commande sans --dry-run'
                )
            )

