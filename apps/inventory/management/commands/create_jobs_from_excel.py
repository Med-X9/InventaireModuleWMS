"""
Commande Django pour créer des jobs à partir d'un fichier Excel.
Regroupe les emplacements par sous_zone et crée les jobs avec leurs assignments.

Format Excel attendu:
- location_reference: Référence de l'emplacement (ex: LO001A001)
- sous_zone_name: Nom de la sous-zone (ex: JOB-0001)
- COMPTAGE 1: Session pour le comptage 1 (ID ou username, ex: EQUIPE-21)
- COMPTAGE 2: Session pour le comptage 2 (ID ou username, ex: EQUIPE-22)

Note: inventory_id et warehouse_id sont passés en paramètre de la commande.

Exemple d'utilisation:
    python manage.py create_jobs_from_excel --file path/to/file.xlsx --inventory-id 2 --warehouse-id 1
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from collections import defaultdict
import logging

from apps.inventory.models import Job, JobDetail, Assigment, Counting, Inventory
from apps.masterdata.models import Location, SousZone, Warehouse
from apps.users.models import UserApp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Crée des jobs à partir d\'un fichier Excel en regroupant les emplacements par sous_zone'

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

    def validate_and_group_data(self, data, inventory_id, warehouse_id):
        """
        Valide les données et les groupe par sous_zone.
        
        Args:
            data: Liste de dictionnaires avec les données Excel
            inventory_id: ID de l'inventaire (passé en paramètre)
            warehouse_id: ID de l'entrepôt (passé en paramètre)
            
        Returns:
            Dict groupé par sous_zone_name avec les sessions pour comptages 1 et 2
        """
        grouped = defaultdict(lambda: {
            'locations': [],
            'session_id': None,
            'inventory_id': None,
            'warehouse_id': None,
            'counting_order': None,
            'sous_zone_name': None
        })
        
        required_fields = ['location_reference', 'sous_zone_name']
        
        for idx, row in enumerate(data, start=2):
            # Vérifier les champs requis
            missing_fields = [field for field in required_fields if not row.get(field)]
            if missing_fields:
                raise CommandError(
                    f"Ligne {idx}: Champs manquants: {', '.join(missing_fields)}"
                )
            
            location_ref = str(row['location_reference']).strip()
            sous_zone_name = str(row['sous_zone_name']).strip()
            
            # Récupérer les sessions pour les comptages 1 et 2
            # Supporte plusieurs noms de colonnes : "COMPTAGE 1", "comptage 1", "counting_1", etc.
            session_1 = None
            session_2 = None
            
            # Chercher la session pour le comptage 1
            for col_name in ['COMPTAGE 1', 'comptage 1', 'COMPTAGE1', 'comptage1', 'counting_1', 'session_1', 'session_id_1']:
                if col_name in row and row[col_name]:
                    session_1 = str(row[col_name]).strip()
                    break
            
            # Chercher la session pour le comptage 2
            for col_name in ['COMPTAGE 2', 'comptage 2', 'COMPTAGE2', 'comptage2', 'counting_2', 'session_2', 'session_id_2']:
                if col_name in row and row[col_name]:
                    session_2 = str(row[col_name]).strip()
                    break
            
            # Créer la clé de regroupement par sous_zone
            # On regroupe par sous_zone uniquement, les sessions seront gérées séparément
            key = sous_zone_name
            
            # Ajouter l'emplacement au groupe
            if key not in grouped:
                grouped[key] = {
                    'locations': [],
                    'sous_zone_name': sous_zone_name,
                    'session_1': session_1,
                    'session_2': session_2
                }
            
            grouped[key]['locations'].append(location_ref)
            # Si une session est spécifiée pour cette ligne, l'utiliser (priorité à la ligne)
            if session_1:
                grouped[key]['session_1'] = session_1
            if session_2:
                grouped[key]['session_2'] = session_2
        
        return grouped

    def get_location_by_reference(self, location_reference, warehouse_id):
        """
        Récupère un emplacement par sa référence.
        
        Args:
            location_reference: Référence de l'emplacement
            warehouse_id: ID de l'entrepôt pour validation
            
        Returns:
            Location object
        """
        try:
            location = Location.objects.get(
                location_reference=location_reference,
                sous_zone__zone__warehouse_id=warehouse_id,
                is_active=True
            )
            return location
        except Location.DoesNotExist:
            raise CommandError(
                f"Emplacement avec la référence '{location_reference}' non trouvé "
                f"pour le warehouse {warehouse_id}"
            )
        except Location.MultipleObjectsReturned:
            raise CommandError(
                f"Plusieurs emplacements trouvés avec la référence '{location_reference}' "
                f"pour le warehouse {warehouse_id}"
            )

    def get_session(self, session_identifier):
        """
        Récupère une session (UserApp de type Mobile) par ID ou username.
        
        Args:
            session_identifier: ID (entier) ou username (texte) de la session
            
        Returns:
            UserApp object ou None
        """
        if not session_identifier:
            return None
        
        # Essayer d'abord comme ID (entier)
        try:
            session_id = int(session_identifier)
            try:
                session = UserApp.objects.get(id=session_id, type='Mobile', is_active=True)
                return session
            except UserApp.DoesNotExist:
                raise CommandError(f"Session avec l'ID {session_id} non trouvée (type Mobile)")
        except (ValueError, TypeError):
            # Si ce n'est pas un entier, traiter comme username
            try:
                session = UserApp.objects.get(username=str(session_identifier), type='Mobile', is_active=True)
                return session
            except UserApp.DoesNotExist:
                raise CommandError(f"Session avec le username '{session_identifier}' non trouvée (type Mobile)")
        
        return None

    def create_job_with_assignments(
        self, 
        inventory_id, 
        warehouse_id, 
        location_ids, 
        session_1=None,
        session_2=None,
        dry_run=False
    ):
        """
        Crée un job avec ses emplacements et assignments pour les comptages 1 et 2.
        
        Args:
            inventory_id: ID de l'inventaire
            warehouse_id: ID de l'entrepôt
            location_ids: Liste des IDs des emplacements
            session_1: Session (UserApp) pour le comptage 1
            session_2: Session (UserApp) pour le comptage 2
            dry_run: Mode test
            
        Returns:
            Dict avec les informations du job créé
        """
        if dry_run:
            return {
                'job_reference': 'JOB-XXXX (simulation)',
                'location_count': len(location_ids),
                'job_details_count': len(location_ids) * 2,
                'assignments_created': (1 if session_1 else 0) + (1 if session_2 else 0)
            }
        
        try:
            # Vérifier que l'inventaire existe
            inventory = Inventory.objects.get(id=inventory_id)
            
            # Vérifier que le warehouse existe
            warehouse = Warehouse.objects.get(id=warehouse_id)
            
            # Vérifier qu'il y a au moins deux comptages pour cet inventaire
            countings = Counting.objects.filter(inventory=inventory).order_by('order')
            if countings.count() < 2:
                raise CommandError(
                    f"Il faut au moins deux comptages pour l'inventaire {inventory.reference}. "
                    f"Comptages trouvés : {countings.count()}"
                )
            
            # Prendre les deux premiers comptages
            counting1 = countings.filter(order=1).first()  # 1er comptage
            counting2 = countings.filter(order=2).first()  # 2ème comptage
            
            if not counting1 or not counting2:
                raise CommandError(
                    f"Comptages d'ordre 1 et 2 requis pour l'inventaire {inventory.reference}"
                )
            
            # Créer le job
            job = Job.objects.create(
                status='EN ATTENTE',
                en_attente_date=timezone.now(),
                warehouse=warehouse,
                inventory=inventory
            )
            
            # Récupérer les locations
            locations = []
            for location_id in location_ids:
                try:
                    location = Location.objects.get(id=location_id)
                    
                    # Vérifier que l'emplacement appartient au warehouse
                    if location.sous_zone.zone.warehouse.id != warehouse_id:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠ Emplacement {location.location_reference} n'appartient pas au warehouse {warehouse_id}"
                            )
                        )
                        continue
                    
                    # Vérifier que l'emplacement n'est pas déjà affecté
                    existing_job_detail = JobDetail.objects.filter(
                        location=location,
                        job__inventory=inventory
                    ).first()
                    
                    if existing_job_detail:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠ Emplacement {location.location_reference} déjà affecté au job {existing_job_detail.job.reference}"
                            )
                        )
                        continue
                    
                    locations.append(location)
                except Location.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ Emplacement avec l'ID {location_id} non trouvé")
                    )
                    continue
            
            if not locations:
                # Supprimer le job créé s'il n'y a pas d'emplacements valides
                job.delete()
                raise CommandError("Aucun emplacement valide pour créer le job")
            
            # Créer les JobDetail pour les deux comptages (1 et 2) pour chaque emplacement
            job_details_created = 0
            assignments_created = []
            
            # Toujours créer les JobDetail pour les deux comptages
            for location in locations:
                # Créer un JobDetail pour le 1er comptage
                JobDetail.objects.create(
                    reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                    location=location,
                    job=job,
                    counting=counting1,
                    status='EN ATTENTE'
                )
                job_details_created += 1
                
                # Créer un JobDetail pour le 2ème comptage
                JobDetail.objects.create(
                    reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
                    location=location,
                    job=job,
                    counting=counting2,
                    status='EN ATTENTE'
                )
                job_details_created += 1
            
            # Créer les affectations pour les comptages 1 et 2
            current_time = timezone.now()
            
            # Assignment pour le comptage 1
            if session_1:
                assignment_1 = Assigment.objects.create(
                    reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                    job=job,
                    counting=counting1,
                    session=session_1,
                    status='PRET',
                    pret_date=current_time,
                    affecte_date=current_time,
                    date_start=current_time
                )
                assignments_created.append(assignment_1.id)
            
            # Assignment pour le comptage 2
            if session_2:
                assignment_2 = Assigment.objects.create(
                    reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
                    job=job,
                    counting=counting2,
                    session=session_2,
                    status='PRET',
                    pret_date=current_time,
                    affecte_date=current_time,
                    date_start=current_time
                )
                assignments_created.append(assignment_2.id)
            
            return {
                'job_id': job.id,
                'job_reference': job.reference,
                'location_count': len(locations),
                'job_details_count': job_details_created,
                'assignments_created': len(assignments_created),
                'assignment_ids': assignments_created
            }
            
        except Inventory.DoesNotExist:
            raise CommandError(f"Inventaire avec l'ID {inventory_id} non trouvé")
        except Warehouse.DoesNotExist:
            raise CommandError(f"Entrepôt avec l'ID {warehouse_id} non trouvé")
        except Exception as e:
            raise CommandError(f"Erreur lors de la création du job: {str(e)}")

    def handle(self, *args, **options):
        file_path = options['file']
        inventory_id = options['inventory_id']
        warehouse_id = options['warehouse_id']
        dry_run = options['dry_run']
        sheet = options['sheet']
        
        self.stdout.write(self.style.SUCCESS(f'📖 Lecture du fichier Excel: {file_path}'))
        self.stdout.write(f'  📦 Inventaire ID: {inventory_id}')
        self.stdout.write(f'  🏭 Warehouse ID: {warehouse_id}')
        
        # Lire le fichier Excel
        try:
            data, headers = self.read_excel_file(file_path, sheet)
            self.stdout.write(self.style.SUCCESS(f'✓ {len(data)} lignes lues'))
            self.stdout.write(f'  Colonnes détectées: {", ".join(headers)}')
        except Exception as e:
            raise CommandError(str(e))
        
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
        
        # Valider et grouper les données
        self.stdout.write(self.style.SUCCESS('\n📊 Validation et regroupement des données...'))
        try:
            grouped_data = self.validate_and_group_data(data, inventory_id, warehouse_id)
            self.stdout.write(self.style.SUCCESS(f'✓ {len(grouped_data)} groupe(s) de sous-zones identifié(s)'))
        except Exception as e:
            raise CommandError(str(e))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 MODE TEST - Aucune donnée ne sera créée\n'))
        
        # Créer les jobs
        jobs_created = 0
        total_locations = 0
        assignments_created = 0
        
        self.stdout.write(self.style.SUCCESS('\n🏭 Création des jobs...\n'))
        
        for sous_zone_name, group_data in grouped_data.items():
            self.stdout.write(
                f"📦 Groupe: Sous-zone '{sous_zone_name}' | "
                f"{len(group_data['locations'])} emplacement(s)"
            )
            
            # Récupérer les IDs des emplacements
            location_ids = []
            for location_ref in group_data['locations']:
                try:
                    location = self.get_location_by_reference(location_ref, warehouse_id)
                    location_ids.append(location.id)
                except CommandError as e:
                    self.stdout.write(self.style.ERROR(f"  ❌ {str(e)}"))
                    continue
            
            if not location_ids:
                self.stdout.write(self.style.WARNING(f"  ⚠ Aucun emplacement valide, groupe ignoré"))
                continue
            
            # Récupérer les sessions pour les comptages 1 et 2
            session_1 = None
            session_2 = None
            
            if group_data.get('session_1'):
                try:
                    session_1 = self.get_session(group_data['session_1'])
                    if session_1:
                        self.stdout.write(
                            f"  👤 Session Comptage 1: {session_1.username} ({session_1.nom} {session_1.prenom})"
                        )
                except CommandError as e:
                    self.stdout.write(self.style.WARNING(f"  ⚠ {str(e)} - Job créé sans session pour comptage 1"))
            
            if group_data.get('session_2'):
                try:
                    session_2 = self.get_session(group_data['session_2'])
                    if session_2:
                        self.stdout.write(
                            f"  👤 Session Comptage 2: {session_2.username} ({session_2.nom} {session_2.prenom})"
                        )
                except CommandError as e:
                    self.stdout.write(self.style.WARNING(f"  ⚠ {str(e)} - Job créé sans session pour comptage 2"))
            
            # Créer le job
            try:
                with transaction.atomic():
                    result = self.create_job_with_assignments(
                        inventory_id=inventory_id,
                        warehouse_id=warehouse_id,
                        location_ids=location_ids,
                        session_1=session_1,
                        session_2=session_2,
                        dry_run=dry_run
                    )
                    
                    if not dry_run:
                        jobs_created += 1
                        total_locations += result['location_count']
                        assignments_created += result['assignments_created']
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ Job {result['job_reference']} créé avec {result['location_count']} emplacement(s) "
                                f"({result['job_details_count']} JobDetail créés)"
                            )
                        )
                        if result['assignments_created'] > 0:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  ✓ {result['assignments_created']} Assignment(s) créé(s) avec statut PRET"
                                )
                            )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  [SIMULATION] Job serait créé avec {result['location_count']} emplacement(s)"
                            )
                        )
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Erreur: {str(e)}"))
                if not dry_run:
                    raise
        
        # Résumé
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODE TEST - Résumé de simulation:'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Résumé de la création:'))
        
        self.stdout.write(f"  • Jobs créés: {jobs_created}")
        self.stdout.write(f"  • Emplacements uniques affectés: {total_locations}")
        self.stdout.write(f"  • Assignments créés: {assignments_created}")
        self.stdout.write(self.style.SUCCESS('='*60))
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n💡 Pour créer réellement les jobs, relancez la commande sans --dry-run'
                )
            )

