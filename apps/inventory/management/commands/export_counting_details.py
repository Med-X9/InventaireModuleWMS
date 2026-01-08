from django.core.management.base import BaseCommand
from django.db.models import Q, Case, When, IntegerField, Value
from django.db.models.functions import Coalesce
from apps.inventory.models import CountingDetail, Job, Inventory
import csv
import os
from datetime import datetime


class Command(BaseCommand):
    help = 'Exporte les CountingDetail agrégés par (job, location, product) avec quantités par ordre de comptage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--inventory-id',
            type=int,
            help='ID de l\'inventaire (optionnel, exporte tout si non spécifié)'
        )
        parser.add_argument(
            '--job-id',
            type=int,
            help='ID du job (optionnel, exporte tout si non spécifié)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='counting_details_aggregated.csv',
            help='Nom du fichier de sortie (défaut: counting_details_aggregated.csv)'
        )

    def handle(self, *args, **options):
        inventory_id = options.get('inventory_id')
        job_id = options.get('job_id')
        output_file = options['output']

        try:
            # Appliquer les filtres de base
            queryset = CountingDetail.objects.select_related(
                'job__inventory',
                'counting',
                'location',
                'product'
            )

            if inventory_id:
                queryset = queryset.filter(job__inventory_id=inventory_id)
                inventory = Inventory.objects.get(id=inventory_id)
                self.stdout.write(f'🟡 Export agrégé pour l\'inventaire {inventory.reference}')

            if job_id:
                queryset = queryset.filter(job_id=job_id)
                job = Job.objects.get(id=job_id)
                self.stdout.write(f'🟡 Export agrégé pour le job {job.reference}')

            if not inventory_id and not job_id:
                self.stdout.write('🟡 Export agrégé de TOUS les CountingDetail (attention: peut être volumineux)')

            # Créer la requête agrégée par (job, location, product)
            # On groupe par ces champs et on calcule les quantités pour chaque counting_order
            from django.db.models import Sum

            aggregated_data = queryset.values(
                'job__reference',
                'location__location_reference',  # Utiliser location_reference
                'product__reference',
                'product__Short_Description',
                'product__Barcode'  # Corriger la casse
            ).annotate(
                # Quantité du 1er comptage (counting.order = 1)
                counting_order_1_qty=Coalesce(
                    Sum('quantity_inventoried', filter=Q(counting__order=1)),
                    Value(0),
                    output_field=IntegerField()
                ),
                # Quantité du 2ème comptage (counting.order = 2)
                counting_order_2_qty=Coalesce(
                    Sum('quantity_inventoried', filter=Q(counting__order=2)),
                    Value(0),
                    output_field=IntegerField()
                )
            ).order_by(
                'job__reference',
                'location__location_reference',
                'product__reference'
            )

            # Compter le nombre de lignes agrégées
            total_count = len(aggregated_data)
            if total_count == 0:
                self.stdout.write(
                    self.style.WARNING('⚠️ Aucune donnée agrégée trouvée avec les critères spécifiés')
                )
                return

            self.stdout.write(f'📊 {total_count} lignes agrégées à exporter')

            # Ouvrir le fichier CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'job_reference',              # Référence du job
                    'location_name',              # Nom de l'emplacement
                    'reference_product',          # Référence du produit
                    'product_short_description',  # Description courte
                    'product_barcode',            # Code barre
                    'counting_order_1_qty',       # Quantité 1er comptage
                    'counting_order_2_qty',       # Quantité 2ème comptage
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                # Traiter chaque ligne agrégée
                processed_count = 0
                for item in aggregated_data:
                    row = {
                        'job_reference': item['job__reference'],
                        'location_name': item.get('location__location_reference', ''),
                        'reference_product': item['product__reference'],
                        'product_short_description': item.get('product__Short_Description', ''),
                        'product_barcode': item.get('product__Barcode', ''),
                        'counting_order_1_qty': item['counting_order_1_qty'],
                        'counting_order_2_qty': item['counting_order_2_qty'],
                    }

                    writer.writerow(row)
                    processed_count += 1

                    # Afficher la progression tous les 1000 enregistrements
                    if processed_count % 1000 == 0:
                        self.stdout.write(f'📝 {processed_count}/{total_count} enregistrements traités...')

            # Résumé final
            file_size = os.path.getsize(output_file)
            self.stdout.write('\n' + '='*60)
            self.stdout.write('EXPORT AGRÉGÉ TERMINÉ AVEC SUCCÈS')
            self.stdout.write(f'Fichier généré: {output_file}')
            self.stdout.write(f'Lignes agrégées exportées: {processed_count}')
            self.stdout.write(f'Taille du fichier: {file_size:,} octets')

            # Statistiques sur les écarts
            with_differences = sum(1 for item in aggregated_data
                                 if item['counting_order_1_qty'] != item['counting_order_2_qty'])
            self.stdout.write(f'Lignes avec écart (qty1 ≠ qty2): {with_differences}')
            self.stdout.write(f'Lignes sans écart (qty1 = qty2): {total_count - with_differences}')

        except Inventory.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f'❌ Inventaire avec ID {inventory_id} non trouvé')
            )
        except Job.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f'❌ Job avec ID {job_id} non trouvé')
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'❌ Erreur inattendue: {str(e)}')
            )
