###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo import _
from odoo.tests.common import HttpCase


class TestWebsiteB2bSignupRequest(HttpCase):

    def setUp(self):
        super().setUp()
        self.data_form = {
            'contact_name': 'Test B2B',
            'phone': '999887766',
            'email_from': 'test@mail.com',
            'partner_name': 'Test company',
            'vat': 'ESA123456789',
            'description': 'B2B test description',
            'name': _('Signup Request'),
        }
        self.endpoint = '/website_form/crm.lead'

    def test_create_crm_lead_b2b_signup_request_form(self):
        response = self.url_open(self.endpoint, data=self.data_form)
        self.assertEquals(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue('id' in result)
        crm_lead = self.env['crm.lead'].browse(result['id'])
        self.assertTrue(crm_lead)
        self.assertEquals(
            crm_lead.contact_name, self.data_form['contact_name'])
        self.assertEquals(crm_lead.phone, self.data_form['phone'])
        self.assertEquals(crm_lead.email_from, self.data_form['email_from'])
        self.assertEquals(
            crm_lead.partner_name, self.data_form['partner_name'])
        self.assertIn(self.data_form['description'], crm_lead.description)
        self.assertIn(self.data_form['vat'], crm_lead.description)
        self.assertFalse(crm_lead.partner_id)
        wizard = self.env['crm.lead2opportunity.partner.mass'].with_context(
            active_ids=crm_lead.ids).create({})
        wizard.mass_convert()
        self.assertTrue(crm_lead.partner_id)
        partner_id = crm_lead.partner_id
        self.assertEquals(partner_id.name, crm_lead.contact_name)
        self.assertEquals(partner_id.phone, crm_lead.phone)
        self.assertEquals(partner_id.email, crm_lead.email_from)
        self.assertIn(self.data_form['vat'], partner_id.comment)
        self.assertIn(self.data_form['description'], partner_id.comment)
