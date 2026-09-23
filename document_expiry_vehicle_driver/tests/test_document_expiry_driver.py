import datetime

from odoo.tests.common import TransactionCase


class TestDocumentExpiryDriver(TransactionCase):
    def setUp(self):
        super().setUp()
        brand = self.env['fleet.vehicle.model.brand'].create({
            'name': 'Test Brand',
        })
        model = self.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': brand.id,
        })
        self.vehicle = self.env['fleet.vehicle'].create({
            'name': 'Test Vehicle',
            'license_plate': '1234ABC',
            'model_id': model.id,
            'odometer_unit': 'kilometers',
        })
        driver1 = self.env['res.partner'].create({
            'name': 'Test Driver 1',
        })
        driver2 = self.env['res.partner'].create({
            'name': 'Test Driver 2',
        })
        self.document_01 = self.env['document.expiry'].with_context(
            default_owner_type='driver'
        ).create({
            'vehicle_id': self.vehicle.id,
            'document_type_driver': 'community',
            'driver_id': driver1.id,
            'document_name': 'Test Document',
            'start_date': datetime.date.today(),
            'end_date': datetime.date.today() + datetime.timedelta(days=365),
        })
        self.document_02 = self.env['document.expiry'].with_context(
            default_owner_type='driver'
        ).create({
            'vehicle_id': self.vehicle.id,
            'document_type_driver': 'community',
            'driver_id': driver2.id,
            'document_name': 'Test Document',
            'start_date': datetime.date.today() - datetime.timedelta(days=365),
            'end_date': datetime.date.today() - datetime.timedelta(days=150),
        })

    def test_document_expiry_driver(self):
        self.assertEqual(self.document_01.document_type_driver, 'community')
        self.assertEqual(self.document_01.status_id.name, 'Valid')
        self.assertEqual(self.document_02.status_id.name, 'Expired')
