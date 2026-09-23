import datetime

from odoo.tests.common import TransactionCase


class TestDocumentExpiryCourse(TransactionCase):
    def setUp(self):
        super().setUp()
        self.category = self.env['hr.course.category'].create({
            'name': 'Test Category',
        })
        self.employee = self.env.ref('hr.employee_hne')
        self.course = self.env['hr.course'].create({
            'name': 'Test Course',
            'category_id': self.category.id,
            'cost': 100,
            'authorized_by': self.employee.id,
        })
        self.document_01 = self.env['document.expiry'].with_context(
            default_owner_type='employee'
        ).create({
            'employee_id': self.employee.id,
            'document_type': 'course',
            'course_id': self.course.id,
            'document_name': 'Test Document',
            'start_date': datetime.date.today(),
            'end_date': datetime.date.today() + datetime.timedelta(days=365),
        })
        self.document_02 = self.env['document.expiry'].with_context(
            default_owner_type='employee'
        ).create({
            'employee_id': self.employee.id,
            'document_type': 'course',
            'course_id': self.course.id,
            'document_name': 'Test Document',
            'start_date': datetime.date.today() - datetime.timedelta(days=365),
            'end_date': datetime.date.today() - datetime.timedelta(days=150),
        })

    def test_document_expiry_course(self):
        self.assertEqual(self.document_01.document_type, 'course')
        self.assertEqual(self.document_01.status_id.name, 'Valid')
        self.assertEqual(self.document_02.status_id.name, 'Expired')
