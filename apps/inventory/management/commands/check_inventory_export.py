"""
Commande de management pour vérifier les données d'un inventaire pour l'export Excel
"""
from django.core.management.base import BaseCommand
from apps.inventory.models import Inventory, Counting, CountingDetail, Job
from django.db.models import Q, Sum, Count


class Command(BaseCommand):
    help = 'Vérifie les données d\'un inventaire pour comprendre les problèmes d\'export Excel'

    def add_arguments(self, parser):
        parser.add_argument(
            'inventory_id',
            type=int,
            help='ID de l\'inventaire à vérifier'
        )

    def handle(self, *args, **options):
        inventory_id = options['inventory_id']
        
        try:
            inventory = Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Inventaire {inventory_id} non trouvé'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n=== VÉRIFICATION INVENTAIRE {inventory_id} ==='))
        self.stdout.write(f'Label: {inventory.label}')
        self.stdout.write(f'Référence: {inventory.reference}')
        self.stdout.write(f'Statut: {inventory.status}\n')
        
        # Vérifier les comptages d'ordre 2 et 3
        counting_order_2 = Counting.objects.filter(
            inventory_id=inventory_id,
            order=2
        ).first()
        
        counting_order_3 = Counting.objects.filter(
            inventory_id=inventory_id,
            order=3
        ).first()
        
        if not counting_order_2:
            self.stdout.write(self.style.ERROR('❌ Comptage d\'ordre 2 non trouvé'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Comptage ordre 2: ID={counting_order_2.id}, Réf={counting_order_2.reference}, Mode={counting_order_2.count_mode}'))
        
        if not counting_order_3:
            self.stdout.write(self.style.ERROR('❌ Comptage d\'ordre 3 non trouvé'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Comptage ordre 3: ID={counting_order_3.id}, Réf={counting_order_3.reference}, Mode={counting_order_3.count_mode}'))
        
        if not counting_order_2 or not counting_order_3:
            return
        
        # Récupérer tous les CountingDetail pour ces comptages
        counting_details = CountingDetail.objects.filter(
            job__inventory_id=inventory_id,
            counting__in=[counting_order_2, counting_order_3],
            product__isnull=False,
            is_deleted=False
        ).select_related(
            'product',
            'location',
            'counting',
            'job'
        ).order_by('product__Internal_Product_Code', 'location__location_reference')
        
        total_counting_details = counting_details.count()
        self.stdout.write(f'\n📊 Total CountingDetail récupérés: {total_counting_details}')
        
        # Grouper par produit
        products_summary = {}
        
        for detail in counting_details:
            product_id = detail.product.id
            product_code = detail.product.Internal_Product_Code
            
            if product_id not in products_summary:
                products_summary[product_id] = {
                    'code': product_code,
                    'reference': detail.product.reference,
                    'description': detail.product.Short_Description or '',
                    'count': 0,
                    'total_qty': 0,
                    'details': []
                }
            
            products_summary[product_id]['count'] += 1
            products_summary[product_id]['total_qty'] += detail.quantity_inventoried
            products_summary[product_id]['details'].append({
                'id': detail.id,
                'qty': detail.quantity_inventoried,
                'location': detail.location.location_reference,
                'counting_order': detail.counting.order,
                'job': detail.job.reference,
                'is_deleted': detail.is_deleted
            })
        
        # Afficher le résumé par produit
        self.stdout.write(f'\n📦 Produits trouvés: {len(products_summary)}\n')
        
        for product_id, data in sorted(products_summary.items(), key=lambda x: x[1]['code']):
            self.stdout.write(self.style.WARNING(f'\n--- Produit: {data["code"]} (ID={product_id}) ---'))
            self.stdout.write(f'Référence: {data["reference"]}')
            self.stdout.write(f'Description: {data["description"]}')
            self.stdout.write(f'Nombre d\'enregistrements: {data["count"]}')
            self.stdout.write(f'Quantité totale consolidée: {data["total_qty"]}')
            self.stdout.write(f'\nDétails des enregistrements:')
            
            for detail_info in data['details']:
                self.stdout.write(
                    f'  • CD ID={detail_info["id"]}, '
                    f'Quantité={detail_info["qty"]}, '
                    f'Emplacement={detail_info["location"]}, '
                    f'Comptage={detail_info["counting_order"]}, '
                    f'Job={detail_info["job"]}, '
                    f'Supprimé={detail_info["is_deleted"]}'
                )
        
        # Vérifier s'il y a des CountingDetail supprimés
        deleted_count = CountingDetail.objects.filter(
            job__inventory_id=inventory_id,
            counting__in=[counting_order_2, counting_order_3],
            product__isnull=False,
            is_deleted=True
        ).count()
        
        if deleted_count > 0:
            self.stdout.write(self.style.WARNING(f'\n⚠️  {deleted_count} CountingDetail supprimés (non inclus dans l\'export)'))
            deleted_details = CountingDetail.objects.filter(
                job__inventory_id=inventory_id,
                counting__in=[counting_order_2, counting_order_3],
                product__isnull=False,
                is_deleted=True
            ).select_related('product', 'location', 'counting', 'job')
            for detail in deleted_details:
                self.stdout.write(
                    f'  • CD ID={detail.id}, Produit={detail.product.Internal_Product_Code if detail.product else "N/A"}, '
                    f'Quantité={detail.quantity_inventoried}, Comptage={detail.counting.order}'
                )
        
        # Vérifier s'il y a des CountingDetail sans produit
        no_product_count = CountingDetail.objects.filter(
            job__inventory_id=inventory_id,
            counting__in=[counting_order_2, counting_order_3],
            product__isnull=True,
            is_deleted=False
        ).count()
        
        if no_product_count > 0:
            self.stdout.write(self.style.WARNING(f'\n⚠️  {no_product_count} CountingDetail sans produit (non inclus dans l\'export)'))
        
        # Vérifier TOUS les CountingDetail pour cet inventaire (tous comptages, tous statuts)
        all_counting_details = CountingDetail.objects.filter(
            job__inventory_id=inventory_id
        ).select_related('product', 'location', 'counting', 'job')
        
        self.stdout.write(f'\n🔍 VÉRIFICATION COMPLÈTE - Tous les CountingDetail pour cet inventaire:')
        self.stdout.write(f'Total (tous comptages, tous statuts): {all_counting_details.count()}')
        
        # Grouper par produit pour voir tous les enregistrements
        all_products_data = {}
        for detail in all_counting_details:
            if detail.product:
                product_id = detail.product.id
                product_code = detail.product.Internal_Product_Code
                
                if product_id not in all_products_data:
                    all_products_data[product_id] = {
                        'code': product_code,
                        'details': []
                    }
                
                all_products_data[product_id]['details'].append({
                    'id': detail.id,
                    'qty': detail.quantity_inventoried,
                    'location': detail.location.location_reference,
                    'counting_order': detail.counting.order,
                    'counting_id': detail.counting.id,
                    'job': detail.job.reference,
                    'is_deleted': detail.is_deleted,
                    'product_isnull': detail.product is None
                })
        
        # Afficher les produits qui ont des différences
        for product_id, data in sorted(all_products_data.items(), key=lambda x: x[1]['code']):
            if product_id in products_summary:
                # Comparer avec les données récupérées
                retrieved_count = products_summary[product_id]['count']
                all_count = len(data['details'])
                if all_count != retrieved_count:
                    self.stdout.write(self.style.ERROR(f'\n⚠️  PRODUIT {data["code"]} (ID={product_id}):'))
                    self.stdout.write(f'  Récupérés pour export: {retrieved_count}')
                    self.stdout.write(f'  Total dans la base: {all_count}')
                    self.stdout.write(f'  Tous les enregistrements:')
                    for detail_info in data['details']:
                        status = '❌ EXCLU' if (detail_info['is_deleted'] or 
                                                 detail_info['counting_order'] not in [2, 3] or
                                                 detail_info['product_isnull']) else '✅ INCLUS'
                        self.stdout.write(
                            f'    {status} CD ID={detail_info["id"]}, '
                            f'Qty={detail_info["qty"]}, '
                            f'Comptage={detail_info["counting_order"]} (ID={detail_info["counting_id"]}), '
                            f'Supprimé={detail_info["is_deleted"]}'
                        )
        
        self.stdout.write(self.style.SUCCESS('\n=== FIN DE LA VÉRIFICATION ===\n'))

