###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime

import psycopg2
from odoo import tools
from odoo.tests.common import TransactionCase


class TestDocumentExpiryPartner(TransactionCase):

    def setUp(self):
        super().setUp()
        today = datetime.date.today()
        admin = self.env.ref('base.user_admin')
        admin.write({
            'groups_id': [(4, self.env.ref(
                'document_expiry_partner.document_partner_expiry_warn').id)],
        })
        self.warn = self.env['document.expiry.status'].create({
            'name': 'Warn',
            'days': 15,
            'color': 'red',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.attachment = self.env['ir.attachment'].create({
            'name': 'Test Attachment',
            'type': 'binary',
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
            'end_date': today - datetime.timedelta(days=30),
        })
        self.document_03 = document_obj.create({
            'owner_type': 'partner',
            'partner_id': self.partner.id,
            'document_type': 'attachment',
            'document_name': 'Document 03',
            'attachment_id': self.attachment.id,
            'start_date': today,
            'end_date': today + datetime.timedelta(days=30),
        })
        self.document_04 = document_obj.create({
            'owner_type': 'partner',
            'partner_id': self.partner.id,
            'document_type': 'custom',
            'document_name': 'Document 04',
            'start_date': today,
            'end_date': today + datetime.timedelta(days=15),
        })
        document_obj.document_expiry_warn_partner()
        self.activity_obj = self.env['mail.activity']

    def test_document_expiry_partner_custom(self):
        self.assertEqual(self.document_01.owner_type, 'partner')
        self.assertEqual(self.document_01.status_id.name, 'Valid')
        self.assertEqual(self.document_02.owner_type, 'partner')
        self.assertEqual(self.document_02.status_id.name, 'Expired')
        self.assertEqual(self.document_04.owner_type, 'partner')
        self.assertEqual(self.document_04.status_id.name, 'Warn')

    def test_document_expiry_partner_attachment(self):
        self.assertEqual(self.document_03.owner_type, 'partner')
        self.assertEqual(self.document_03.status_id.name, 'Valid')
        self.assertEqual(self.document_03.document_type, 'attachment')
        self.assertEqual(self.document_03.attachment_id.id, self.attachment.id)

    def test_document_expiry_partner_activity(self):
        activity_type = self.env.ref(
            'document_expiry_partner.activity_document_expired_warn_partner')
        domain = [
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.partner.id),
            ('activity_type_id', '=', activity_type.id),
        ]
        activities = self.activity_obj.search(domain)
        self.assertEqual(len(activities), 1)
        self.assertIn('documentation in state', activities.summary)
        self.env['document.expiry'].document_expiry_warn_partner()
        self.assertEqual(self.activity_obj.search_count(domain), 1)

    def test_document_expiry_partner_does_not_warn_generic_documents(self):
        generic_document = self.env['document.expiry'].create({
            'owner_type': 'other',
            'document_type': 'custom',
            'document_name': 'Generic document',
            'start_date': datetime.date.today() - datetime.timedelta(days=30),
            'end_date': datetime.date.today() - datetime.timedelta(days=1),
        })
        self.env['document.expiry'].document_expiry_warn_partner()
        activity_type = self.env.ref(
            'document_expiry_partner.activity_document_expired_warn_partner')
        self.assertFalse(self.activity_obj.search([
            ('activity_type_id', '=', activity_type.id),
            ('res_model', '=', 'document.expiry'),
            ('res_id', '=', generic_document.id),
        ]))

    def test_document_expiry_partner_action_and_views(self):
        action = self.env.ref(
            'document_expiry_partner.action_partner_document_expiry')
        self.assertEqual(action.res_model, 'document.expiry')
        self.assertIn("'owner_type', '=', 'partner'", action.domain)
        self.assertIn("'default_owner_type': 'partner'", action.context)
        partner_view = self.env.ref(
            'document_expiry_partner.view_partner_form')
        self.assertIn('editable="bottom"', partner_view.arch_db)

    def test_document_expiry_partner_selection_ondelete(self):
        field = self.env['document.expiry']._fields['owner_type']
        self.assertEqual(field.ondelete['partner'], 'set null')

    def test_document_expiry_partner_prevents_partner_deletion(self):
        partner = self.env['res.partner'].create({
            'name': 'Protected partner',
        })
        self.env['document.expiry'].create({
            'owner_type': 'partner',
            'partner_id': partner.id,
            'document_type': 'custom',
            'document_name': 'Protected document',
            'start_date': datetime.date.today(),
            'end_date': datetime.date.today() + datetime.timedelta(days=1),
        })
        with self.assertRaises(psycopg2.IntegrityError) as error:
            with tools.mute_logger('odoo.sql_db'), self.cr.savepoint():
                partner.unlink()
        self.assertIn(
            'violates foreign key constraint', error.exception.pgerror)
