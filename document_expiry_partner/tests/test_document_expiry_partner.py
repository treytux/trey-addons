import datetime

from odoo.tests.common import TransactionCase


class TestDocumentExpiryPartner(TransactionCase):
    def setUp(self):
        super().setUp()
        today = datetime.date.today()
        admin = self.env.ref('base.user_admin')
        admin.write({
            'groups_id': [(4, self.env.ref(
                'document_expiry_partner.document_partner_expiry_warn').id)]
        })
        self.partner = self.env.ref('base.res_partner_12')
        self.attachment = self.env['ir.attachment'].create({
            'name': 'Test Attachment',
            'type': 'binary'
        })
        document_obj = self.env['document.expiry']
        self.document_01 = document_obj.create({
            'owner_type': 'partner',
            'partner_id': self.partner.id,
            'document_type': 'custom',
            'document_name': 'Document 01',
            'start_date': today,
            'end_date': today + datetime.timedelta(days=30),
        })
        self.document_02 = document_obj.create({
            'owner_type': 'partner',
            'partner_id': self.partner.id,
            'document_type': 'custom',
            'document_name': 'Document 02',
            'start_date': today - datetime.timedelta(days=60),
            'end_date': today - datetime.timedelta(days=30)
        })
        self.document_03 = document_obj.create({
            'owner_type': 'partner',
            'partner_id': self.partner.id,
            'document_type': 'attachment',
            'document_name': 'Document 03',
            'attachment_id': self.attachment.id,
            'start_date': today,
            'end_date': today + datetime.timedelta(days=30)
        })
        self.document_04 = document_obj.create({
            'owner_type': 'partner',
            'partner_id': self.partner.id,
            'document_type': 'attachment',
            'document_name': 'Document 04',
            'attachment_id': self.attachment.id,
            'start_date': today - datetime.timedelta(days=60),
            'end_date': today - datetime.timedelta(days=30),
        })
        document_obj.document_expiry_warn_partner()
        self.activity_obj = self.env['mail.activity']

    def test_document_expiry_partner_custom(self):
        self.assertEqual(self.document_01.partner_id.id, self.partner.id)
        self.assertEqual(self.document_01.status_id.name, 'Valid')
        self.assertEqual(self.document_02.partner_id.id, self.partner.id)
        self.assertEqual(self.document_02.status_id.name, 'Expired')

    def test_document_expiry_partner_attachment(self):
        self.assertEqual(self.document_03.partner_id.id, self.partner.id)
        self.assertEqual(self.document_03.status_id.name, 'Valid')
        self.assertEqual(self.document_04.partner_id.id, self.partner.id)
        self.assertEqual(self.document_04.status_id.name, 'Expired')

    def test_document_expiry_partner_activity(self):
        activity = self.activity_obj.search([('res_id', '=', self.partner.id)])
        self.assertEqual(activity.res_id, self.partner.id)
        self.assertIn('documentation in state', activity.summary)
