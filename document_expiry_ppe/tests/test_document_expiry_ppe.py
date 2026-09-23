###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestDocumentExpiryPPE(TransactionCase):

    def setUp(self):
        super().setUp()
        self.today = fields.Date.today()
        self.employee = self.env.ref('hr.employee_hne')
        self.other_employee = self.env['hr.employee'].create({
            'name': 'Other Employee',
        })
        self.product = self.env['product.product'].create({
            'name': 'Face Shield',
            'is_personal_equipment': True,
        })
        self.request = self.env['hr.personal.equipment.request'].create({
            'employee_id': self.employee.id,
        })
        self.ppe = self.env['hr.personal.equipment'].create({
            'product_id': self.product.id,
            'equipment_request_id': self.request.id,
        })
        other_request = self.env['hr.personal.equipment.request'].create({
            'employee_id': self.other_employee.id,
        })
        self.other_ppe = self.env['hr.personal.equipment'].create({
            'product_id': self.product.id,
            'equipment_request_id': other_request.id,
        })
        self.document_01 = self.env['document.expiry'].create({
            'owner_type': 'employee',
            'employee_id': self.employee.id,
            'document_type': 'ppe',
            'ppe_id': self.ppe.id,
            'start_date': self.today,
            'end_date': self.today + timedelta(days=30),
        })
        self.document_02 = self.env['document.expiry'].create({
            'owner_type': 'employee',
            'employee_id': self.employee.id,
            'document_type': 'ppe',
            'ppe_id': self.ppe.id,
            'start_date': self.today - timedelta(days=60),
            'end_date': self.today - timedelta(days=30),
        })

    def test_document_expiry_ppe(self):
        self.assertEqual(
            self.ppe.name, f'Face Shield to {self.employee.name}')
        self.assertEqual(self.document_01.document_type, 'ppe')
        self.assertEqual(self.document_01.employee_id, self.employee)
        self.assertEqual(self.document_01.ppe_id, self.ppe)
        self.assertEqual(self.document_01.status_id.name, 'Valid')
        self.assertEqual(self.document_02.document_type, 'ppe')
        self.assertEqual(self.document_02.employee_id, self.employee)
        self.assertEqual(self.document_02.ppe_id, self.ppe)
        self.assertEqual(self.document_02.status_id.name, 'Expired')

    def test_document_type_selection_contains_ppe(self):
        document_types = dict(
            self.env['document.expiry']._selection_document_type())
        self.assertEqual(document_types['ppe'], 'PPE Allocation')

    def test_ppe_document_requires_employee(self):
        with self.assertRaisesRegex(
                ValidationError, 'requires an employee'):
            self.env['document.expiry'].create({
                'owner_type': 'employee',
                'document_type': 'ppe',
                'ppe_id': self.ppe.id,
                'start_date': self.today,
                'end_date': self.today + timedelta(days=30),
            })

    def test_ppe_document_requires_ppe(self):
        with self.assertRaisesRegex(
                ValidationError, 'requires a PPE allocation'):
            self.env['document.expiry'].create({
                'owner_type': 'employee',
                'employee_id': self.employee.id,
                'document_type': 'ppe',
                'start_date': self.today,
                'end_date': self.today + timedelta(days=30),
            })

    def test_ppe_document_requires_ppe_from_employee(self):
        with self.assertRaisesRegex(
                ValidationError, 'must belong to the selected employee'):
            self.env['document.expiry'].create({
                'owner_type': 'employee',
                'employee_id': self.employee.id,
                'document_type': 'ppe',
                'ppe_id': self.other_ppe.id,
                'start_date': self.today,
                'end_date': self.today + timedelta(days=30),
            })

    def test_ppe_document_write_requires_ppe_from_employee(self):
        with self.assertRaisesRegex(
                ValidationError, 'must belong to the selected employee'):
            self.document_01.write({'ppe_id': self.other_ppe.id})
