###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests import common


class TestAgreementAcceptance(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.agreement = self.env['agreement.template'].create({
            'name': 'privacy',
            'document': 'privacy.pdf'
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.agreement_acceptance = self.env['agreement.acceptance'].create({
            'agreement_template': self.agreement.id,
            'state': 'unaccepted',
            'partner_id': self.partner.id,
        })
        self.partner_contact = self.env['res.partner'].create({
            'name': 'Test partner contact',
            'is_company': False,
        })

    def test_agreement_acceptance(self):
        name_test = 'privacy'
        document = 'privacy.pdf'
        self.agreement.document = 'privacy.pdf'
        self.assertEqual(self.agreement.name, name_test)
        self.assertEqual(self.agreement.document, document)
        self.assertEqual(
            self.agreement_acceptance.agreement_template.name, name_test)
        self.assertEqual(
            self.agreement_acceptance.agreement_template.document, document)
        self.assertEqual(
            self.agreement_acceptance.agreement_template.id,
            self.agreement.id)
        self.assertEqual(self.agreement_acceptance.state, 'unaccepted')
        self.agreement_acceptance.state = 'accepted'
        self.assertEqual(self.agreement_acceptance.state, 'accepted')
        self.agreement_acceptance.acceptance_date = fields.Date.today()
        self.assertEqual(
            self.agreement_acceptance.acceptance_date,
            fields.Date.today())
        self.assertEqual(
            self.agreement_acceptance.partner_id.name, 'Test partner')
        self.agreement_acceptance.partner_id.name = 'New partner name'
        self.assertNotEqual(
            self.agreement_acceptance.partner_id.name, 'Test partner')
        childs = []
        childs.append(self.partner_contact.id)
        self.partner.child_ids = childs
        self.agreement_acceptance.acceptance_partner_id = self.partner_contact
        self.assertEqual(
            self.agreement_acceptance.acceptance_partner_id.id,
            self.partner_contact.id)
        self.partner_contact.name = 'Test2'
        self.assertEqual(
            self.agreement_acceptance.acceptance_partner_id.name,
            self.partner_contact.name)
