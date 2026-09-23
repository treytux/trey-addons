import datetime

from odoo.tests.common import TransactionCase


class TestDocumentExpiryVehicle(TransactionCase):
    def setUp(self):
        super().setUp()
        admin = self.env.ref('base.user_admin')
        admin.write({
            'groups_id': [(4, self.env.ref(
                'document_expiry_vehicle.document_vehicle_expiry_warn').id)]
        })
        self.warn = self.env['document.expiry.status'].create({
            'name': 'Warn',
            'days': 15,
            'color': 'red',
        })
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
        self.attachment = self.env['ir.attachment'].create({
            'name': 'Test Attachment',
            'type': 'binary'
        })
        self.document_obj = self.env['document.expiry']
        self.document_01 = self.document_obj.create({
            'owner_type': 'vehicle',
            'vehicle_id': self.vehicle.id,
            'document_type': 'custom',
            'document_name': 'Test Document',
            'start_date': datetime.date.today(),
            'end_date': datetime.date.today() + datetime.timedelta(days=30),
        })
        self.document_02 = self.document_obj.create({
            'owner_type': 'vehicle',
            'vehicle_id': self.vehicle.id,
            'document_type': 'custom',
            'document_name': 'Test Document',
            'start_date': datetime.date.today() - datetime.timedelta(days=60),
            'end_date': datetime.date.today() - datetime.timedelta(days=30),
        })
        self.document_03 = self.document_obj.create({
            'owner_type': 'vehicle',
            'vehicle_id': self.vehicle.id,
            'document_type': 'attachment',
            'document_name': 'Test Document',
            'attachment_id': self.attachment.id,
            'start_date': datetime.date.today(),
            'end_date': datetime.date.today() + datetime.timedelta(days=30),
        })
        self.document_04 = self.document_obj.create({
            'owner_type': 'vehicle',
            'vehicle_id': self.vehicle.id,
            'document_type': 'custom',
            'document_name': 'Test Document',
            'start_date': datetime.date.today(),
            'end_date': datetime.date.today() + datetime.timedelta(days=15),
        })
        self.document_obj.document_expiry_warn_vehicle()
        self.activity_obj = self.env['mail.activity']

    def test_document_expiry_vehicle(self):
        self.assertEqual(self.document_01.owner_type, 'vehicle')
        self.assertEqual(self.document_01.status_id.name, 'Valid')
        self.assertEqual(self.document_02.owner_type, 'vehicle')
        self.assertEqual(self.document_02.status_id.name, 'Expired')
        self.assertEqual(self.document_04.owner_type, 'vehicle')
        self.assertEqual(self.document_04.status_id.name, 'Warn')

    def test_document_expiry_vehicle_activity(self):
        document_02_activity = self.activity_obj.search(
            [('res_id', '=', self.document_02.vehicle_id.id)])
        self.assertEqual(
            document_02_activity.res_id,
            self.document_02.vehicle_id.id)
        self.assertIn('documentation in state', document_02_activity.summary)
        document_04_activity = self.activity_obj.search(
            [('res_id', '=', self.document_04.vehicle_id.id)])
        self.assertEqual(
            document_04_activity.res_id,
            self.document_04.vehicle_id.id)
        self.assertIn('documentation in state', document_04_activity.summary)

    def test_document_expiry_vehicle_attachment(self):
        self.assertEqual(self.document_03.owner_type, 'vehicle')
        self.assertEqual(self.document_03.status_id.name, 'Valid')
        self.assertEqual(self.document_03.document_type, 'attachment')
        self.assertEqual(self.document_03.attachment_id.id, self.attachment.id)
