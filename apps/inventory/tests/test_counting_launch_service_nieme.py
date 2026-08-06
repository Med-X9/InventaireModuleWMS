"""
Tests unitaires — n-ième comptage (CountingLaunchService).

Couvre :
- lancement 3e (comptage existant order=3)
- lancement 4e / 5e (duplication order 3)
- réutilisation d'un comptage déjà créé pour un autre emplacement
- prérequis JobDetail TERMINE et écart non résolu
"""
from django.test import TestCase
from django.utils import timezone

from apps.inventory.exceptions.counting_exceptions import (
    CountingNotFoundError,
    CountingValidationError,
)
from apps.inventory.models import (
    Assigment,
    ComptageSequence,
    Counting,
    CountingDetail,
    EcartComptage,
    Inventory,
    Job,
    JobDetail,
)
from apps.inventory.services.counting_launch_service import CountingLaunchService
from apps.masterdata.models import (
    Account,
    Location,
    LocationType,
    SousZone,
    Warehouse,
    Zone,
    ZoneType,
)
from apps.users.models import UserApp


def _ref(model_cls) -> str:
    """Génère une référence unique pour les modèles ReferenceMixin."""
    return model_cls().generate_reference(model_cls.REFERENCE_PREFIX)


class CountingLaunchServiceNiemeTestCase(TestCase):
    """Tests du lancement de comptages d'ordre >= 3 (n-ième)."""

    def setUp(self) -> None:
        self.service = CountingLaunchService()

        self.account = Account.objects.create(
            reference='ACC-NIE',
            account_name='Compte Nieme',
            account_statuts='ACTIVE',
        )
        self.zone_type = ZoneType.objects.create(
            reference='ZT-NIE',
            type_name='ZT Nieme',
            status='ACTIVE',
        )
        self.warehouse = Warehouse.objects.create(
            reference='WH-NIE',
            warehouse_name='Entrepot Nieme',
            warehouse_type='CENTRAL',
            status='ACTIVE',
        )
        self.zone = Zone.objects.create(
            reference='Z-NIE',
            warehouse=self.warehouse,
            zone_name='Zone Nieme',
            zone_type=self.zone_type,
            zone_status='ACTIVE',
        )
        self.sous_zone = SousZone.objects.create(
            reference='SZ-NIE',
            sous_zone_name='SZ Nieme',
            zone=self.zone,
            sous_zone_status='ACTIVE',
        )
        self.location_type = LocationType.objects.create(
            reference='LT-NIE',
            name='Type Nieme',
        )
        self.location = Location.objects.create(
            reference='LOC-NIE-1',
            location_reference='LOC-NIE-0001',
            sous_zone=self.sous_zone,
            location_type=self.location_type,
        )

        self.inventory = Inventory.objects.create(
            label='Inventaire N-ieme',
            date=timezone.now(),
            status='EN COURS',
        )
        self.counting1 = Counting.objects.create(
            order=1,
            count_mode='en vrac',
            reference=_ref(Counting),
            inventory=self.inventory,
        )
        self.counting2 = Counting.objects.create(
            order=2,
            count_mode='en vrac',
            reference=_ref(Counting),
            inventory=self.inventory,
        )
        self.counting3 = Counting.objects.create(
            order=3,
            count_mode='en vrac',
            reference=_ref(Counting),
            inventory=self.inventory,
            unit_scanned=True,
            entry_quantity=True,
        )

        self.job = Job.objects.create(
            status='VALIDE',
            warehouse=self.warehouse,
            inventory=self.inventory,
        )

        # JobDetails des comptages 1 et 2 terminés (prérequis 3e)
        for counting in (self.counting1, self.counting2):
            JobDetail.objects.create(
                reference=_ref(JobDetail),
                location=self.location,
                job=self.job,
                counting=counting,
                status='TERMINE',
            )
            Assigment.objects.create(
                reference=_ref(Assigment),
                job=self.job,
                counting=counting,
                status='TERMINE',
            )

        self.session = UserApp.objects.create(
            username='mobile-nieme',
            type='Mobile',
            nom='Mobile',
            prenom='Nieme',
        )

        self._create_unresolved_ecart(self.location)

    def _create_unresolved_ecart(self, location: Location) -> EcartComptage:
        """Attache un écart non résolu (final_result null) à l'emplacement du job."""
        detail = CountingDetail.objects.create(
            reference=_ref(CountingDetail),
            counting=self.counting1,
            location=location,
            job=self.job,
            quantity_inventoried=10,
        )
        detail2 = CountingDetail.objects.create(
            reference=_ref(CountingDetail),
            counting=self.counting2,
            location=location,
            job=self.job,
            quantity_inventoried=15,
        )
        ecart = EcartComptage.objects.create(
            reference=_ref(EcartComptage),
            inventory=self.inventory,
            resolved=False,
            final_result=None,
        )
        ComptageSequence.objects.create(
            reference=_ref(ComptageSequence),
            ecart_comptage=ecart,
            sequence_number=1,
            counting_detail=detail,
            quantity=detail.quantity_inventoried,
        )
        ComptageSequence.objects.create(
            reference=_ref(ComptageSequence),
            ecart_comptage=ecart,
            sequence_number=2,
            counting_detail=detail2,
            quantity=detail2.quantity_inventoried,
            ecart_with_previous=5,
        )
        return ecart

    def _complete_counting_for_location(self, counting: Counting, location: Location) -> None:
        """Passe JobDetail + assignment du comptage en TERMINE pour l'emplacement."""
        job_detail = JobDetail.objects.get(
            job=self.job,
            location=location,
            counting=counting,
        )
        job_detail.status = 'TERMINE'
        job_detail.save(update_fields=['status'])

        assignment = Assigment.objects.filter(
            job=self.job,
            counting=counting,
        ).first()
        if assignment:
            assignment.status = 'TERMINE'
            assignment.save(update_fields=['status'])

    def test_rejects_invalid_ids(self) -> None:
        with self.assertRaises(CountingValidationError):
            self.service.launch_counting(0, self.location.id, self.session.id)
        with self.assertRaises(CountingValidationError):
            self.service.launch_counting(self.job.id, 0, self.session.id)
        with self.assertRaises(CountingValidationError):
            self.service.launch_counting(self.job.id, self.location.id, 0)

    def test_rejects_without_unresolved_ecart(self) -> None:
        EcartComptage.objects.filter(inventory=self.inventory).update(
            resolved=True,
            final_result=10,
        )
        with self.assertRaises(CountingValidationError) as ctx:
            self.service.launch_counting(
                self.job.id,
                self.location.id,
                self.session.id,
            )
        self.assertIn('écart non résolu', str(ctx.exception))

    def test_launch_third_counting_uses_existing_order_three(self) -> None:
        initial = Counting.objects.filter(inventory=self.inventory).count()

        result = self.service.launch_counting(
            self.job.id,
            self.location.id,
            self.session.id,
        )

        self.assertEqual(result['counting']['order'], 3)
        self.assertFalse(result['counting']['new_counting_created'])
        self.assertTrue(result['assignment']['created'])
        self.assertEqual(result['assignment']['status'], 'TRANSFERT')
        self.assertTrue(result['job_detail']['created'])
        self.assertEqual(
            Counting.objects.filter(inventory=self.inventory).count(),
            initial,
        )
        self.assertTrue(
            JobDetail.objects.filter(
                job=self.job,
                location=self.location,
                counting=self.counting3,
            ).exists()
        )
        assignment = Assigment.objects.get(job=self.job, counting=self.counting3)
        self.assertEqual(assignment.session_id, self.session.id)

    def test_launch_third_requires_orders_one_and_two_completed(self) -> None:
        jd1 = JobDetail.objects.get(
            job=self.job,
            location=self.location,
            counting=self.counting1,
        )
        jd1.status = 'EN ATTENTE'
        jd1.save(update_fields=['status'])

        with self.assertRaises(CountingValidationError) as ctx:
            self.service.launch_counting(
                self.job.id,
                self.location.id,
                self.session.id,
            )
        self.assertIn('3ème comptage', str(ctx.exception))

    def test_launch_fourth_duplicates_counting_three_config(self) -> None:
        self.service.launch_counting(
            self.job.id,
            self.location.id,
            self.session.id,
        )
        self._complete_counting_for_location(self.counting3, self.location)

        before = Counting.objects.filter(inventory=self.inventory).count()
        result = self.service.launch_counting(
            self.job.id,
            self.location.id,
            self.session.id,
        )

        self.assertEqual(result['counting']['order'], 4)
        self.assertTrue(result['counting']['new_counting_created'])
        self.assertEqual(
            Counting.objects.filter(inventory=self.inventory).count(),
            before + 1,
        )
        new_counting = Counting.objects.get(id=result['counting']['id'])
        self.assertEqual(new_counting.order, 4)
        self.assertEqual(new_counting.count_mode, self.counting3.count_mode)
        self.assertEqual(new_counting.unit_scanned, self.counting3.unit_scanned)
        self.assertEqual(new_counting.entry_quantity, self.counting3.entry_quantity)

    def test_cannot_launch_fourth_if_third_not_completed(self) -> None:
        self.service.launch_counting(
            self.job.id,
            self.location.id,
            self.session.id,
        )
        # JobDetail order 3 reste EN ATTENTE

        with self.assertRaises(CountingValidationError) as ctx:
            self.service.launch_counting(
                self.job.id,
                self.location.id,
                self.session.id,
            )
        self.assertIn("ordre 3 n'est pas terminé", str(ctx.exception))

    def test_launch_fifth_after_fourth_completed(self) -> None:
        self.service.launch_counting(
            self.job.id,
            self.location.id,
            self.session.id,
        )
        self._complete_counting_for_location(self.counting3, self.location)

        r4 = self.service.launch_counting(
            self.job.id,
            self.location.id,
            self.session.id,
        )
        counting4 = Counting.objects.get(id=r4['counting']['id'])
        self._complete_counting_for_location(counting4, self.location)

        result = self.service.launch_counting(
            self.job.id,
            self.location.id,
            self.session.id,
        )

        self.assertEqual(result['counting']['order'], 5)
        self.assertTrue(result['counting']['new_counting_created'])
        counting5 = Counting.objects.get(id=result['counting']['id'])
        self.assertEqual(counting5.count_mode, self.counting3.count_mode)

    def test_reuses_existing_higher_order_created_for_other_location(self) -> None:
        """Si order 4 existe déjà (autre emplacement), on le réutilise sans re-dupliquer."""
        location2 = Location.objects.create(
            reference='LOC-NIE-2',
            location_reference='LOC-NIE-0002',
            sous_zone=self.sous_zone,
            location_type=self.location_type,
        )
        for counting in (self.counting1, self.counting2):
            JobDetail.objects.create(
                reference=_ref(JobDetail),
                location=location2,
                job=self.job,
                counting=counting,
                status='TERMINE',
            )
        self._create_unresolved_ecart(location2)

        # Emplacement 1 → 3e, puis 4e (crée Counting order 4)
        self.service.launch_counting(
            self.job.id,
            self.location.id,
            self.session.id,
        )
        self._complete_counting_for_location(self.counting3, self.location)
        r4_loc1 = self.service.launch_counting(
            self.job.id,
            self.location.id,
            self.session.id,
        )
        counting4_id = r4_loc1['counting']['id']
        countings_before = Counting.objects.filter(inventory=self.inventory).count()

        # Emplacement 2 → 3e, terminer, puis 4e doit réutiliser le même Counting
        self.service.launch_counting(
            self.job.id,
            location2.id,
            self.session.id,
        )
        self._complete_counting_for_location(self.counting3, location2)

        r4_loc2 = self.service.launch_counting(
            self.job.id,
            location2.id,
            self.session.id,
        )

        self.assertEqual(r4_loc2['counting']['order'], 4)
        self.assertFalse(r4_loc2['counting']['new_counting_created'])
        self.assertEqual(r4_loc2['counting']['id'], counting4_id)
        self.assertEqual(
            Counting.objects.filter(inventory=self.inventory).count(),
            countings_before,
        )

    def test_missing_order_three_raises_not_found(self) -> None:
        self.counting3.delete()
        with self.assertRaises(CountingNotFoundError) as ctx:
            self.service.launch_counting(
                self.job.id,
                self.location.id,
                self.session.id,
            )
        self.assertIn('ordre 3', str(ctx.exception))

    def test_find_highest_counting_order_with_jobdetail(self) -> None:
        self.assertEqual(
            self.service._find_highest_counting_order_with_jobdetail(
                self.job,
                self.location,
            ),
            2,
        )
        JobDetail.objects.create(
            reference=_ref(JobDetail),
            location=self.location,
            job=self.job,
            counting=self.counting3,
            status='EN ATTENTE',
        )
        self.assertEqual(
            self.service._find_highest_counting_order_with_jobdetail(
                self.job,
                self.location,
            ),
            3,
        )

    def test_recreates_missing_previous_jobdetail_if_assignment_termine(self) -> None:
        """
        _ensure_previous_countings_completed recrée le JobDetail manquant
        en TERMINE si l'assignment du comptage précédent est TERMINE.
        """
        self.service.launch_counting(
            self.job.id,
            self.location.id,
            self.session.id,
        )
        assignment3 = Assigment.objects.get(job=self.job, counting=self.counting3)
        assignment3.status = 'TERMINE'
        assignment3.save(update_fields=['status'])
        JobDetail.objects.filter(
            job=self.job,
            location=self.location,
            counting=self.counting3,
        ).delete()

        # Appel direct : prérequis du 4e comptage (ordre 3 manquant)
        self.service._ensure_previous_countings_completed(
            self.job.id,
            self.location.id,
            target_order=4,
        )

        recreated = JobDetail.objects.filter(
            job=self.job,
            location=self.location,
            counting=self.counting3,
        ).first()
        self.assertIsNotNone(recreated)
        self.assertEqual(recreated.status, 'TERMINE')

    def test_relaunch_order_three_if_jobdetail_missing(self) -> None:
        """Sans JobDetail d'ordre 3, le service relance le 3e (pas le 4e)."""
        self.service.launch_counting(
            self.job.id,
            self.location.id,
            self.session.id,
        )
        assignment3 = Assigment.objects.get(job=self.job, counting=self.counting3)
        assignment3.status = 'TERMINE'
        assignment3.save(update_fields=['status'])
        JobDetail.objects.filter(
            job=self.job,
            location=self.location,
            counting=self.counting3,
        ).delete()

        result = self.service.launch_counting(
            self.job.id,
            self.location.id,
            self.session.id,
        )

        self.assertEqual(result['counting']['order'], 3)
        self.assertFalse(result['counting']['new_counting_created'])
        recreated = JobDetail.objects.filter(
            job=self.job,
            location=self.location,
            counting=self.counting3,
        ).first()
        self.assertIsNotNone(recreated)
        self.assertEqual(recreated.status, 'EN ATTENTE')
