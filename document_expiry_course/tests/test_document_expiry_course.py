###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestDocumentExpiryCourse(TransactionCase):

    def setUp(self):
        super().setUp()
        self.category = self.env['hr.course.category'].create({
            'name': 'Test Category',
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
        })
        self.course = self.env['hr.course'].create({
            'name': 'Test Course',
            'category_id': self.category.id,
        })
        today = fields.Date.today()
        self.document_01 = self.env['document.expiry'].with_context(
            default_owner_type='employee').create({
                'employee_id': self.employee.id,
                'document_type': 'course',
                'course_id': self.course.id,
                'document_name': 'Test Document',
                'start_date': today,
                'end_date': today + timedelta(days=365),
            })
        self.document_02 = self.env['document.expiry'].with_context(
            default_owner_type='employee').create({
                'employee_id': self.employee.id,
                'document_type': 'course',
                'course_id': self.course.id,
                'document_name': 'Test Document',
                'start_date': today - timedelta(days=365),
                'end_date': today - timedelta(days=150),
            })

    def test_document_expiry_course(self):
        self.assertEqual(self.document_01.document_type, 'course')
        self.assertEqual(self.document_01.course_id, self.course)
        self.assertEqual(
            self.document_01.status_id,
            self.env.ref('document_expiry.document_expiry_status_valid'))
        self.assertEqual(
            self.document_02.status_id,
            self.env.ref('document_expiry.document_expiry_status_expired'))

    def test_course_document_type_is_available_without_context(self):
        DocumentExpiry = self.env['document.expiry']
        default_types = dict(DocumentExpiry._selection_document_type())
        employee_types = dict(DocumentExpiry.with_context(
            default_owner_type='employee')._selection_document_type())
        self.assertIn('course', default_types)
        self.assertIn('course', employee_types)

    def test_course_document_created_from_employee(self):
        today = fields.Date.today()
        employee = self.env['hr.employee'].create({
            'name': 'Employee with course document',
        })
        employee.write({
            'expiry_docs_ids': [Command.create({
                'owner_type': 'employee',
                'document_type': 'course',
                'course_id': self.course.id,
                'document_name': 'Course document from employee',
                'start_date': today,
                'end_date': today + timedelta(days=365),
            })],
        })
        self.assertEqual(employee.expiry_docs_ids.course_id, self.course)
