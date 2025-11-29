"""
Commande Django pour importer des articles (produits) depuis un fichier Excel/CSV
Usage: python manage.py import_products --file path/to/file.xlsx
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.masterdata.admin import ProductResource
from import_export.formats.base_formats import XLSX, CSV, XLS
import os


class Command(BaseCommand):
    help = 'Importe des articles (produits) depuis un fichier Excel/CSV'

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
        resource = ProductResource()

        # Valider les données
        self.stdout.write('📋 Validation des données...')
        result = resource.import_data(dataset, dry_run=True, raise_errors=False)

        # Afficher les erreurs de validation
        if result.has_errors():
            self.stdout.write(self.style.ERROR('\n❌ Erreurs de validation:'))
            for error in result.base_errors:
                self.stdout.write(self.style.ERROR(f'  - {error.error}'))
            for line, errors in result.row_errors():
                self.stdout.write(
                    self.style.ERROR(f'  - Ligne {line}: {", ".join([str(e.error) for e in errors])}')
                )
            raise CommandError('Des erreurs de validation ont été détectées. Corrigez le fichier et réessayez.')

        # Si dry-run, arrêter ici
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Validation réussie! {len(dataset)} lignes sont valides.'
                )
            )
            self.stdout.write('ℹ️  Mode test activé - aucune donnée n\'a été importée.')
            return

        # Importer les données
        self.stdout.write('\n📥 Importation des données...')
        try:
            with transaction.atomic():
                result = resource.import_data(dataset, dry_run=False, raise_errors=True)
                
                # Afficher les résultats
                self.stdout.write(self.style.SUCCESS('\n✅ Import terminé avec succès!'))
                self.stdout.write(f'  - Lignes importées: {result.totals.get("new", 0)}')
                self.stdout.write(f'  - Lignes mises à jour: {result.totals.get("update", 0)}')
                self.stdout.write(f'  - Lignes ignorées: {result.totals.get("skip", 0)}')
                self.stdout.write(f'  - Erreurs: {result.totals.get("error", 0)}')
                
        except Exception as e:
            raise CommandError(f'Erreur lors de l\'importation: {str(e)}')

