import datetime

from odoo.tests.common import TransactionCase


class TestDocumentExpiryPPE(TransactionCase):
    def setUp(self):
        super().setUp()
        today = datetime.date.today()
        self.ppe = self.env.ref('hr_employee_ppe.hr_employee_ppe_equipment2')
        self.employee = self.env.ref('hr.employee_hne')
        self.document_01 = self.env['document.expiry'].with_context(
            default_owner_type='employee'
        ).create({
            'employee_id': self.employee.id,
            'document_type': 'ppe',
            'ppe_id': self.ppe.id,
            'start_date': today,
            'end_date': today + datetime.timedelta(days=30),
        })
        self.document_02 = self.env['document.expiry'].with_context(
            default_owner_type='employee'
        ).create({
            'employee_id': self.employee.id,
            'document_type': 'ppe',
            'ppe_id': self.ppe.id,
            'start_date': today - datetime.timedelta(days=60),
            'end_date': today - datetime.timedelta(days=30),
        })

    def test_document_expiry_ppe(self):
        ppe_name = f'Face Shield to {self.employee.name}'
        self.assertEqual(self.document_01.document_type, 'ppe')
        self.assertEqual(self.document_01.ppe_id.name, ppe_name)
        self.assertEqual(self.document_01.status_id.name, 'Valid')
        self.assertEqual(self.document_02.document_type, 'ppe')
        self.assertEqual(self.document_02.ppe_id.name, ppe_name)
        self.assertEqual(self.document_02.status_id.name, 'Expired')
