"""
Commande Django pour importer des emplacements depuis un fichier Excel/CSV
Usage: python manage.py import_locations --file path/to/file.xlsx
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.masterdata.admin import LocationResource
from import_export.formats.base_formats import XLSX, CSV, XLS
import os


class Command(BaseCommand):
    help = 'Importe des emplacements depuis un fichier Excel/CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Chemin vers le fichier Excel/CSV à importer'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : valide les données sans les importer'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']

        # Vérifier que le fichier existe
        if not os.path.exists(file_path):
            raise CommandError(f'Le fichier "{file_path}" n\'existe pas.')

        # Détecter le format du fichier
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.xlsx':
            file_format = XLSX()
        elif file_extension == '.xls':
            file_format = XLS()
        elif file_extension == '.csv':
            file_format = CSV()
        else:
            raise CommandError(
                f'Format de fichier non supporté: {file_extension}. '
                'Formats supportés: .xlsx, .xls, .csv'
            )

        # Lire le fichier
        try:
            with open(file_path, 'rb') as f:
                dataset = file_format.create_dataset(f.read())
        except Exception as e:
            raise CommandError(f'Erreur lors de la lecture du fichier: {str(e)}')

        # Créer la ressource
        resource = LocationResource()

        # VALIDATION COMPLÈTE - MODE TOUT OU RIEN
        self.stdout.write('🔍 Validation complète des données (mode tout ou rien)...')

        # Collecter toutes les erreurs de validation
        all_errors = []

        # Convertir le dataset en dictionnaires si nécessaire
        rows_as_dicts = []
        for row in dataset:
            if isinstance(row, dict):
                rows_as_dicts.append(row)
            elif hasattr(row, '__iter__') and not isinstance(row, (str, bytes)):
                # Convertir tuple ou autre itérable en dict en utilisant les headers
                row_dict = {}
                headers = dataset.headers if hasattr(dataset, 'headers') else None
                if headers:
                    for j, value in enumerate(row):
                        if j < len(headers):
                            row_dict[headers[j]] = value
                rows_as_dicts.append(row_dict)
            else:
                rows_as_dicts.append({})

        # Vérifier chaque ligne individuellement pour collecter TOUTES les erreurs
        for i, row in enumerate(rows_as_dicts, start=2):  # Commencer à 2 car ligne 1 = headers
            try:
                # Essayer de valider cette ligne spécifique
                # On utilise before_import_row qui fait la validation personnalisée
                resource.before_import_row(row)

            except ValueError as e:
                all_errors.append(f'Ligne {i}: {str(e)}')
            except Exception as e:
                all_errors.append(f'Ligne {i}: Erreur inattendue - {str(e)}')

        # Si des erreurs ont été trouvées, arrêter immédiatement
        if all_errors:
            self.stdout.write(self.style.ERROR('\n❌ Erreurs de validation détectées:'))
            # Limiter l'affichage à 50 erreurs maximum pour éviter un output trop long
            for error in all_errors[:50]:
                self.stdout.write(self.style.ERROR(f'  - {error}'))

            if len(all_errors) > 50:
                self.stdout.write(self.style.ERROR(f'  ... et {len(all_errors) - 50} autres erreurs'))

            raise CommandError(
                f'❌ ÉCHEC DE VALIDATION - Mode "tout ou rien" activé. '
                f'{len(all_errors)} erreurs trouvées. Corrigez le fichier et réessayez.'
            )

        # Validation Django-import-export standard
        result = resource.import_data(dataset, dry_run=True, raise_errors=False)
        if result.has_errors():
            self.stdout.write(self.style.ERROR('\n❌ Erreurs de validation Django:'))
            for error in result.base_errors:
                all_errors.append(f'Erreur générale: {error.error}')
            for line, errors in result.row_errors():
                for error in errors:
                    all_errors.append(f'Ligne {line}: {str(error.error)}')

            if all_errors:
                for error in all_errors[:50]:
                    self.stdout.write(self.style.ERROR(f'  - {error}'))
                if len(all_errors) > 50:
                    self.stdout.write(self.style.ERROR(f'  ... et {len(all_errors) - 50} autres erreurs'))

                raise CommandError(
                    f'❌ ÉCHEC DE VALIDATION - Mode "tout ou rien" activé. '
                    f'{len(all_errors)} erreurs trouvées. Corrigez le fichier et réessayez.'
                )

        # Si dry-run, arrêter ici
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ VALIDATION RÉUSSIE! Toutes les {len(dataset)} lignes sont valides.'
                )
            )
            self.stdout.write('ℹ️  Mode test activé - aucune donnée n\'a été importée.')
            return

        # IMPORT COMPLET - TOUT OU RIEN
        self.stdout.write('\n🚀 Importation complète des données (mode tout ou rien)...')
        try:
            with transaction.atomic():
                # Importer avec raise_errors=True pour arrêter dès la première erreur
                result = resource.import_data(dataset, dry_run=False, raise_errors=True)

                # Afficher les résultats
                self.stdout.write(self.style.SUCCESS('\n✅ IMPORT RÉUSSI - TOUTES LES DONNÉES ONT ÉTÉ IMPORTÉES!'))
                self.stdout.write(f'  - Lignes importées: {result.totals.get("new", 0)}')
                self.stdout.write(f'  - Lignes mises à jour: {result.totals.get("update", 0)}')
                self.stdout.write(f'  - Lignes ignorées: {result.totals.get("skip", 0)}')

        except Exception as e:
            # En cas d'erreur pendant l'import, tout sera rollback automatiquement grâce à transaction.atomic()
            raise CommandError(f'❌ ÉCHEC D\'IMPORT - Mode "tout ou rien" activé. Rien n\'a été importé. Erreur: {str(e)}')

