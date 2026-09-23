import datetime

from odoo.tests.common import TransactionCase


class TestDocumentExpiryMedical(TransactionCase):
    def setUp(self):
        super().setUp()
        today = datetime.date.today()
        self.employee = self.env.ref('hr.employee_hne')
        examination = self.env['hr.employee.medical.examination']
        self.medical_examination = examination.with_context(
            default_owner_type='employee'
        ).create({
            'name': self.employee.name,
            'employee_id': self.employee.id,
            'date': datetime.date.today(),
            'year': datetime.date.year
        })
        self.document_01 = self.env['document.expiry'].with_context(
            default_owner_type='employee'
        ).create({
            'employee_id': self.employee.id,
            'document_type': 'medical',
            'examination_id': self.medical_examination.id,
            'document_name': 'Medical Examination',
            'start_date': today,
            'end_date': today + datetime.timedelta(days=30)
        })
        self.document_02 = self.env['document.expiry'].with_context(
            default_owner_type='employee'
        ).create({
            'employee_id': self.employee.id,
            'document_type': 'medical',
            'examination_id': self.medical_examination.id,
            'document_name': 'Medical Examination',
            'start_date': today - datetime.timedelta(days=60),
            'end_date': today - datetime.timedelta(days=30)
        })

    def test_document_expiry_medical(self):
        self.assertEqual(self.document_01.status_id.name, 'Valid')
        self.assertEqual(self.document_02.status_id.name, 'Expired')
