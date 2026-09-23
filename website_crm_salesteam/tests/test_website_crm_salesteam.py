###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from types import SimpleNamespace

from odoo.tests import common


class TestWebsiteCrmSalesteam(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.website = self.env['website'].get_current_website()
        self.crm_team_model = self.env['crm.team']
        self.crm_lead_model = self.env['crm.lead']
        self.default_team = self.crm_team_model.create({
            'name': 'Default Website Team',
            'use_leads': True,
            'company_id': self.env.company.id,
        })
        self.website_team = self.crm_team_model.create({
            'name': 'Website Sales Team',
            'use_leads': True,
            'company_id': self.env.company.id,
        })
        self.website.write({
            'crm_default_team_id': self.default_team.id,
            'crm_default_user_id': self.env.user.id,
        })

    def _build_request(self):
        return SimpleNamespace(website=self.website)

    def test_website_form_input_filter_uses_website_salesteam(self):
        self.website.salesteam_id = self.website_team
        request = self._build_request()
        values = self.crm_lead_model.website_form_input_filter(request, {})
        self.assertEqual(values['team_id'], self.website_team.id)

    def test_website_form_input_filter_keeps_existing_team(self):
        self.website.salesteam_id = False
        request = self._build_request()
        values = self.crm_lead_model.website_form_input_filter(
            request,
            {'team_id': self.default_team.id},
        )
        self.assertEqual(values['team_id'], self.default_team.id)

    def test_website_form_input_filter_uses_default_team_wo_salesteam(self):
        self.website.salesteam_id = False
        request = self._build_request()
        values = self.crm_lead_model.website_form_input_filter(request, {})
        self.assertEqual(values['team_id'], self.default_team.id)
