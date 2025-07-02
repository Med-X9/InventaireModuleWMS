from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Location, SousZone, Zone, Warehouse, LocationType

# Create your tests here.

class LocationDetailAPITest(APITestCase):
    def setUp(self):
        self.warehouse = Warehouse.objects.create(reference='WH-001', warehouse_name='Entrepôt Test', warehouse_type='CENTRAL', status='ACTIVE')
        self.zone = Zone.objects.create(reference='Z-001', warehouse=self.warehouse, zone_name='Zone Test', zone_type_id=1, description='Zone de test', zone_status='ACTIVE')
        self.sous_zone = SousZone.objects.create(reference='SZ-001', sous_zone_name='SousZone Test', zone=self.zone, description='Sous-zone de test', sous_zone_status='ACTIVE')
        self.location_type = LocationType.objects.create(reference='LT-001', name='Type Test')
        self.location = Location.objects.create(reference='LOC-001', location_reference='L-001', sous_zone=self.sous_zone, location_type=self.location_type, is_active=True)

    def test_location_detail_success(self):
        url = reverse('masterdata:location-detail', args=[self.location.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.location.id)
        self.assertEqual(response.data['location_reference'], self.location.location_reference)

    def test_location_detail_not_found(self):
        url = reverse('masterdata:location-detail', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
