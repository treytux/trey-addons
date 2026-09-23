###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime

from odoo.tests.common import TransactionCase


class TestDocumentExpiryEmployee(TransactionCase):
    def setUp(self):
        super().setUp()
        admin = self.env.ref('base.user_admin')
        admin.write({
            'groups_id': [(4, self.env.ref(
                'document_expiry_employee.document_employee_expiry_warn').id)]
        })
        self.warn = self.env['document.expiry.status'].create({
            'name': 'Warn',
            'days': 15,
            'color': 'red',
        })
        self.employee = self.env.ref('hr.employee_hne')
        self.attachment = self.env['ir.attachment'].create({
            'name': 'Test Attachment',
            'type': 'binary'
        })
        self.document_obj = self.env['document.expiry']
        self.document_01 = self.document_obj.create({
            'owner_type': 'employee',
            'employee_id': self.employee.id,
            'document_type': 'custom',
            'document_name': 'Test Document',
            'start_date': datetime.date.today(),
            'end_date': datetime.date.today() + datetime.timedelta(days=30),
        })
        self.document_02 = self.document_obj.create({
            'owner_type': 'employee',
            'employee_id': self.employee.id,
            'document_type': 'custom',
            'document_name': 'Test Document',
            'start_date': datetime.date.today() - datetime.timedelta(days=60),
            'end_date': datetime.date.today() - datetime.timedelta(days=30),
        })
        self.document_03 = self.document_obj.create({
            'owner_type': 'employee',
            'employee_id': self.employee.id,
            'document_type': 'attachment',
            'document_name': 'Test Document',
            'attachment_id': self.attachment.id,
            'start_date': datetime.date.today(),
            'end_date': datetime.date.today() + datetime.timedelta(days=30),
        })
        self.document_04 = self.document_obj.create({
            'owner_type': 'employee',
            'employee_id': self.employee.id,
            'document_type': 'custom',
            'document_name': 'Test Document',
            'start_date': datetime.date.today(),
            'end_date': datetime.date.today() + datetime.timedelta(days=15),
        })
        self.document_obj.document_expiry_warn_employee()
        self.activity_obj = self.env['mail.activity']

    def test_document_expiry_employee(self):
        self.assertEqual(self.document_01.owner_type, 'employee')
        self.assertEqual(self.document_01.status_id.name, 'Valid')
        self.assertEqual(self.document_02.owner_type, 'employee')
        self.assertEqual(self.document_02.status_id.name, 'Expired')
        self.assertEqual(self.document_04.owner_type, 'employee')
        self.assertEqual(self.document_04.status_id.name, 'Warn')

    def test_document_expiry_employee_activity(self):
        document_02_activity = self.activity_obj.search(
            [('res_id', '=', self.document_02.employee_id.id)])
        self.assertEqual(
            document_02_activity.res_id,
            self.document_02.employee_id.id)
        self.assertIn('documentation in state', document_02_activity.summary)
        document_04_activity = self.activity_obj.search(
            [('res_id', '=', self.document_04.employee_id.id)])
        self.assertEqual(
            document_04_activity.res_id,
            self.document_04.employee_id.id)
        self.assertIn('documentation in state', document_04_activity.summary)

    def test_document_expiry_employee_attachment(self):
        self.assertEqual(self.document_03.owner_type, 'employee')
        self.assertEqual(self.document_03.status_id.name, 'Valid')
        self.assertEqual(self.document_03.document_type, 'attachment')
        self.assertEqual(self.document_03.attachment_id.id, self.attachment.id)
