"""
Génère counting_details_payload.json avec les location_id récupérés depuis JobDetail (job donné).

Exemple:
    python manage.py build_counting_payload_from_job_details --job-id 181 --counting-id 171 --assignment-id 4330 --product-start 137708 --product-end 137803 --output counting_details_payload.json
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.inventory.models import JobDetail


class Command(BaseCommand):
    help = 'Génère un payload de counting details avec location_id depuis JobDetail (job donné)'

    def add_arguments(self, parser):
        parser.add_argument('--job-id', type=int, default=181, help='ID du job')
        parser.add_argument('--counting-id', type=int, default=171, help='ID du comptage')
        parser.add_argument('--assignment-id', type=int, default=4330, help='ID de l\'affectation')
        parser.add_argument('--product-start', type=int, default=137708, help='Premier product_id (inclus)')
        parser.add_argument('--product-end', type=int, default=137803, help='Dernier product_id (inclus)')
        parser.add_argument(
            '--output',
            type=str,
            default='counting_details_payload.json',
            help='Fichier JSON de sortie (chemin relatif à la racine du projet)',
        )

    def handle(self, *args, **options):
        job_id = options['job_id']
        counting_id = options['counting_id']
        assignment_id = options['assignment_id']
        product_start = options['product_start']
        product_end = options['product_end']
        output_path = Path(options['output'])
        if not output_path.is_absolute():
            # Racine du projet = parent du dossier contenant manage.py
            base = Path(__file__).resolve().parents[4]
            output_path = base / output_path

        location_ids = list(
            JobDetail.objects.filter(
                job_id=job_id,
                counting_id=counting_id,
            )
            .order_by('location__location_reference')
            .values_list('location_id', flat=True)
        )

        if not location_ids:
            raise CommandError(
                f'Aucun JobDetail trouvé pour job_id={job_id}, counting_id={counting_id}. '
                'Vérifiez les IDs en base.'
            )

        n_products = product_end - product_start + 1
        # Une entrée par emplacement (toutes les locations du job). product_id cycle si plus d'emplacements que de produits.
        quantities = [(i * 11 % 61) * 8 + 5 for i in range(len(location_ids))]

        data = [
            {
                'counting_id': counting_id,
                'location_id': location_ids[i],
                'quantity_inventoried': quantities[i],
                'assignment_id': assignment_id,
                'product_id': product_start + (i % n_products),
            }
            for i in range(len(location_ids))
        ]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        self.stdout.write(
            self.style.SUCCESS(
                f'Fichier écrit: {output_path} ({len(data)} entrées, location_id depuis JobDetail job_id={job_id}, counting_id={counting_id})'
            )
        )
