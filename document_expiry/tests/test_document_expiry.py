import datetime

from odoo.tests.common import TransactionCase


class TestDocumentExpiry(TransactionCase):
    def setUp(self):
        super().setUp()
        self.today = datetime.date.today()
        self.status = self.env['document.expiry.status'].create({
            'name': 'Test Status',
            'color': 'green',
            'warn': True,
            'days': 3,
        })
        self.document_01 = self.env['document.expiry'].create({
            'document_type': 'custom',
            'document_name': 'Test Document',
            'start_date': self.today,
            'end_date': self.today + datetime.timedelta(10),
        })
        self.document_02 = self.env['document.expiry'].create({
            'document_type': 'custom',
            'document_name': 'Test Document',
            'start_date': self.today - datetime.timedelta(10),
            'end_date': self.today - datetime.timedelta(5),
        })
        self.document_03 = self.env['document.expiry'].create({
            'document_type': 'custom',
            'document_name': 'Test Document',
            'start_date': self.today - datetime.timedelta(4),
            'end_date': self.today,
        })

    def test_document_expiry_status(self):
        self.assertEqual(self.document_01.status_id.name, 'Valid')
        self.assertEqual(self.document_02.status_id.name, 'Expired')
        self.assertEqual(self.document_03.status_id.name, 'Test Status')
