import datetime

from odoo.tests.common import TransactionCase


class TestDocumentExpiryInspection(TransactionCase):
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
        self.inspection = self.env['fleet.vehicle.inspection'].create({
            'name': 'Test Inspection',
            'vehicle_id': self.vehicle.id,
            'odometer_unit': 'kilometers',
            'date_inspected': datetime.date.today(),
        })
        self.document_01 = self.env['document.expiry'].with_context(
            default_owner_type='vehicle'
        ).create({
            'vehicle_id': self.vehicle.id,
            'document_type': 'brakes',
            'inspection_id': self.inspection.id,
            'document_name': 'Test Document',
            'start_date': datetime.date.today(),
            'end_date': datetime.date.today() + datetime.timedelta(days=365),
        })
        self.document_02 = self.env['document.expiry'].with_context(
            default_owner_type='vehicle'
        ).create({
            'vehicle_id': self.vehicle.id,
            'document_type': 'brakes',
            'inspection_id': self.inspection.id,
            'document_name': 'Test Document',
            'start_date': datetime.date.today() - datetime.timedelta(days=365),
            'end_date': datetime.date.today() - datetime.timedelta(days=150),
        })

    def test_document_expiry_course(self):
        self.assertEqual(self.document_01.document_type, 'brakes')
        self.assertEqual(self.document_01.status_id.name, 'Valid')
        self.assertEqual(self.document_02.status_id.name, 'Expired')
