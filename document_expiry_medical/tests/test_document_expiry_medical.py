###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestDocumentExpiryMedical(TransactionCase):

    def setUp(self):
        super().setUp()
        self.today = fields.Date.today()
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
        })
        self.medical_examination = self.env[
            'hr.employee.medical.examination'
        ].create({
            'name': self.employee.name,
            'employee_id': self.employee.id,
            'date': self.today,
            'year': str(self.today.year),
        })
        self.employee.write({
            'expiry_docs_ids': [
                Command.create({
                    'owner_type': 'employee',
                    'employee_id': self.employee.id,
                    'document_type': 'medical',
                    'examination_id': self.medical_examination.id,
                    'document_name': 'Medical Examination',
                    'start_date': self.today,
                    'end_date': self.today + timedelta(days=30)}),
                Command.create({
                    'owner_type': 'employee',
                    'employee_id': self.employee.id,
                    'document_type': 'medical',
                    'examination_id': self.medical_examination.id,
                    'document_name': 'Medical Examination',
                    'start_date': self.today - timedelta(days=60),
                    'end_date': self.today - timedelta(days=30)}),
            ],
        })
        valid_end_date = self.today + timedelta(days=30)
        expired_end_date = self.today - timedelta(days=30)
        self.document_01 = self.employee.expiry_docs_ids.filtered(
            lambda document: document.end_date == valid_end_date)
        self.document_02 = self.employee.expiry_docs_ids.filtered(
            lambda document: document.end_date == expired_end_date)

    def test_document_expiry_medical(self):
        document_expiry = self.env['document.expiry']
        document_type = dict(document_expiry._selection_document_type())
        employee_document_type = dict(document_expiry.with_context(
            default_owner_type='employee')._selection_document_type())
        self.assertNotIn('medical', document_type)
        self.assertIn('medical', employee_document_type)
        self.assertEqual(self.document_01.document_type, 'medical')
        self.assertEqual(self.document_01.employee_id, self.employee)
        self.assertEqual(
            self.document_01.examination_id, self.medical_examination)
        self.assertEqual(self.document_01.status_id.name, 'Valid')
        self.assertEqual(self.document_02.status_id.name, 'Expired')
