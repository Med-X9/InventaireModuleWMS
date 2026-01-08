from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.inventory.models import Job, Assigment, EcartComptage, ComptageSequence, CountingDetail, Inventory
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Crée les ComptageSequence manquantes pour les CountingDetail existants d\'un inventaire'

    def add_arguments(self, parser):
        parser.add_argument(
            'inventory_id',
            type=int,
            help='ID de l\'inventaire pour lequel créer les séquences manquantes'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test : simule les changements sans les appliquer réellement'
        )

    def handle(self, *args, **options):
        inventory_id = options['inventory_id']
        dry_run = options['dry_run']

        try:
            # Valider que l'inventaire existe
            inventory = Inventory.objects.get(id=inventory_id)
            self.stdout.write(f'🟡 Inventaire {inventory.reference} (ID: {inventory.id})')

            # Récupérer tous les jobs liés à cet inventaire
            jobs = Job.objects.filter(inventory=inventory)

            if not jobs.exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Aucun job trouvé pour l\'inventaire {inventory.reference}')
                )
                return

            self.stdout.write(f'🟡 Analyse de {jobs.count()} jobs liés à l\'inventaire {inventory.reference}')

            # Statistiques globales
            total_counting_details_found = 0
            total_sequences_created = 0
            total_ecarts_created = 0

            # Traiter chaque job
            for job in jobs:
                self.stdout.write(f'\n🏭 Job {job.reference} (ID: {job.id})')

                # Récupérer tous les CountingDetail de ce job
                counting_details = CountingDetail.objects.filter(job=job)

                if not counting_details.exists():
                    self.stdout.write(f'  ℹ️ Aucun CountingDetail trouvé pour ce job')
                    continue

                self.stdout.write(f'  📊 {counting_details.count()} CountingDetail trouvé(s)')

                job_sequences_created = 0
                job_ecarts_created = 0

                # Traiter chaque CountingDetail
                for counting_detail in counting_details:
                    total_counting_details_found += 1

                    # Vérifier si ce CountingDetail a déjà une ComptageSequence
                    existing_sequence = ComptageSequence.objects.filter(
                        counting_detail=counting_detail
                    ).first()

                    if existing_sequence:
                        continue  # Passer silencieusement les existants

                    # Créer la ComptageSequence manquante avec EcartComptage
                    if dry_run:
                        self.stdout.write(
                            f'  ✅ [DRY-RUN] SERAIT créé séquence + écart pour {counting_detail.reference}'
                        )
                        job_sequences_created += 1
                        total_sequences_created += 1
                    else:
                        try:
                            with transaction.atomic():
                                # 1. Créer ou récupérer l'EcartComptage
                                ecart, created = self.get_or_create_ecart_comptage(counting_detail)
                                if created:
                                    job_ecarts_created += 1
                                    total_ecarts_created += 1

                                # 2. Déterminer le numéro de séquence
                                sequence_number = self.get_next_sequence_number(ecart, counting_detail)

                                # 3. Calculer l'écart avec la séquence précédente
                                ecart_with_previous = self.calculate_ecart_with_previous(ecart, sequence_number, counting_detail.quantity_inventoried)

                                # 4. Créer la ComptageSequence
                                sequence = ComptageSequence.objects.create(
                                    ecart_comptage=ecart,
                                    counting_detail=counting_detail,
                                    sequence_number=sequence_number,
                                    quantity=counting_detail.quantity_inventoried,
                                    ecart_with_previous=ecart_with_previous
                                )

                                # 5. Générer la référence
                                sequence.reference = sequence.generate_reference(ComptageSequence.REFERENCE_PREFIX)
                                sequence.save()

                                # 6. Mettre à jour l'écart
                                ecart.total_sequences = sequence_number
                                ecart.stopped_sequence = sequence_number

                                # Calculer le résultat final si possible
                                if sequence_number >= 2:
                                    final_result = self.calculate_consensus_result(ecart)
                                    if final_result is not None:
                                        ecart.final_result = final_result
                                        ecart.resolved = True

                                ecart.save()

                            job_sequences_created += 1
                            total_sequences_created += 1

                            self.stdout.write(
                                f'  ✅ Créé séquence {sequence.reference} pour {counting_detail.reference} (Écart: {ecart.reference})'
                            )

                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'  ❌ Erreur création séquence pour {counting_detail.reference}: {str(e)}'
                                )
                            )
                            logger.error(f"Erreur création séquence pour CountingDetail {counting_detail.id}: {str(e)}")

                # Résumé par job
                if job_sequences_created > 0:
                    self.stdout.write(
                        f'  📈 Job {job.reference} : {job_sequences_created} séquence(s) créé(es), '
                        f'{job_ecarts_created} écart(s) créé(s)'
                    )

            # Résumé final
            self.stdout.write('\n' + '='*60)
            mode = "[DRY-RUN] " if dry_run else ""
            self.stdout.write(f'{mode}RÉSUMÉ GLOBAL DE CRÉATION DES SÉQUENCES:')
            self.stdout.write(f'Jobs traités: {jobs.count()}')
            self.stdout.write(f'CountingDetail analysés: {total_counting_details_found}')
            self.stdout.write(f'ComptageSequence créées: {total_sequences_created}')
            self.stdout.write(f'EcartComptage créés: {total_ecarts_created}')

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'\n🔍 [DRY-RUN] {total_sequences_created} séquences SERAIENT créées')
                )
            else:
                if total_sequences_created > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'\n✅ {total_sequences_created} ComptageSequence créées avec succès')
                    )
                    if total_ecarts_created > 0:
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ {total_ecarts_created} EcartComptage créés')
                        )

                    # Suggérer de lancer le calcul des écarts maintenant
                    self.stdout.write(
                        self.style.WARNING(
                            f'\n💡 Vous pouvez maintenant lancer le calcul des écarts :\n'
                            f'   python manage.py calculate_ecarts_and_resolve_zero_differences {inventory_id}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('\n⚠️ Aucune séquence n\'a été créée (toutes existent déjà)')
                    )

        except Inventory.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f'❌ Inventaire avec ID {inventory_id} non trouvé')
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'❌ Erreur inattendue: {str(e)}')
            )
            logger.error(f"Erreur lors de la création des séquences: {str(e)}", exc_info=True)

    def get_or_create_ecart_comptage(self, counting_detail):
        """
        Récupère ou crée un EcartComptage pour le CountingDetail.
        Regroupement par (produit + emplacement + inventaire)
        """
        from apps.inventory.models import EcartComptage

        product = counting_detail.product
        location = counting_detail.location
        inventory = counting_detail.job.inventory

        if not product or not location:
            raise ValueError("Produit et emplacement requis pour créer un EcartComptage")

        # Chercher un écart existant
        existing_ecart = EcartComptage.objects.filter(
            counting_sequences__counting_detail__product=product,
            counting_sequences__counting_detail__location=location,
            inventory=inventory
        ).distinct().first()

        if existing_ecart:
            # Vérifier qu'il n'est pas résolu
            if existing_ecart.resolved:
                raise ValueError(f"L'écart {existing_ecart.reference} est déjà résolu")
            return existing_ecart, False

        # Créer un nouvel écart
        ecart = EcartComptage.objects.create(
            inventory=inventory,
            total_sequences=0,
            resolved=False,
            final_result=None
        )
        ecart.reference = ecart.generate_reference(EcartComptage.REFERENCE_PREFIX)
        ecart.save()

        return ecart, True

    def get_next_sequence_number(self, ecart, counting_detail):
        """
        Détermine le prochain numéro de séquence pour cet écart.
        """
        # Vérifier si ce CountingDetail a déjà une séquence dans cet écart
        existing_sequence = ecart.counting_sequences.filter(
            counting_detail=counting_detail
        ).first()

        if existing_sequence:
            # Mise à jour d'une séquence existante
            return existing_sequence.sequence_number
        else:
            # Nouvelle séquence
            return ecart.total_sequences + 1

    def calculate_ecart_with_previous(self, ecart, sequence_number, current_quantity):
        """
        Calcule l'écart avec la séquence précédente.
        """
        if sequence_number <= 1:
            return None

        # Trouver la séquence précédente
        previous_sequence = ecart.counting_sequences.filter(
            sequence_number=sequence_number - 1
        ).first()

        if previous_sequence:
            return abs(current_quantity - previous_sequence.quantity)

        return None

    def calculate_consensus_result(self, ecart):
        """
        Calcule le résultat final si consensus possible.
        Version simplifiée basée sur la logique de l'API.
        """
        sequences = list(ecart.counting_sequences.order_by('sequence_number'))

        if len(sequences) < 2:
            return None

        # Prendre la dernière séquence
        current_quantity = sequences[-1].quantity

        # Vérifier si elle correspond à au moins une précédente
        previous_quantities = [seq.quantity for seq in sequences[:-1]]

        if current_quantity in previous_quantities:
            return current_quantity

        return None
