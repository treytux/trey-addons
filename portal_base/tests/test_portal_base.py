###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import HttpCase


class TestPortalBase(HttpCase):

    def setUp(self):
        super().setUp()
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test@test.com',
            'password': 'test123',
        })
        self.IrConfig = self.env['ir.config_parameter'].sudo()

    def test_portal_controller_load_proper_template(self):
        self.authenticate('demo', 'demo')
        response = self.url_open('/my/conditions/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Payment term:', response.text)
        self.assertIn('Customer payment mode:', response.text)
        self.assertIn('My account conditions', response.text)
        self.assertIn('Pricelist:', response.text)

    def test_portal_controller_loads_user_partner(self):
        self.authenticate(self.user.login, 'test123')
        response = self.url_open('/my/conditions')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user.partner_id.name, response.text)

    def test_edit_portal_details_active_shows_link(self):
        self.authenticate(self.user.login, 'test123')
        response = self.url_open('/my/home')
        self.assertEqual(response.status_code, 200)
        self.assertIn('/my/conditions', response.text)
        self.assertIn('Details', response.text)

    def test_edit_portal_details_inactive_hides_link(self):
        self.IrConfig.set_param('portal_base.edit_portal_details', 'False')
        response = self.url_open('/my/home')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('/my/conditions', response.text)
        self.assertNotIn('Details', response.text)
        response = self.url_open('/my/conditions')
        self.assertEqual(response.status_code, 200)
        self.assertIn('/my/conditions', response.text)
        self.assertNotIn('Details', response.text)
