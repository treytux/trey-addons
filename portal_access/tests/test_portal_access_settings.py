###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPortalAccessSettings(TransactionCase):

    def setUp(self):
        super().setUp()
        self.website = self.env['website'].get_current_website()
        self.portal_user = self.env['res.users'].create({
            'name': 'Portal User',
            'login': 'portal_user',
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        self.employee_user = self.env['res.users'].create({
            'name': 'Employee User',
            'login': 'employee_user',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        self.settings = self.env['res.config.settings'].create({})

    def test_get_portal_access_scope(self):
        self.website.portal_access_scope = 'portal'
        self.assertEqual(self.website.get_portal_access_scope(), 'portal')

    def test_portal_blocked(self):
        self.website.portal_access_scope = 'portal'
        self.assertFalse(self.website.get_portal_access(self.portal_user))
        self.assertTrue(self.website.get_portal_access(self.employee_user))

    def test_employee_blocked(self):
        self.website.portal_access_scope = 'employee'
        self.assertFalse(self.website.get_portal_access(self.employee_user))
        self.assertTrue(self.website.get_portal_access(self.portal_user))

    def test_both_blocked(self):
        self.website.portal_access_scope = 'both'
        self.assertFalse(self.website.get_portal_access(self.portal_user))
        self.assertFalse(self.website.get_portal_access(self.employee_user))

    def test_no_blocking(self):
        self.website.portal_access_scope = False
        self.assertTrue(self.website.get_portal_access(self.portal_user))
        self.assertTrue(self.website.get_portal_access(self.employee_user))

    def test_settings_get_values(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'website.portal_access_scope', 'employee')
        values = self.settings.get_values()
        self.assertEqual(values['portal_access_scope'], 'employee')

    def test_settings_set_values(self):
        self.settings.portal_access_scope = 'portal'
        self.settings.set_values()
        value = self.env['ir.config_parameter'].sudo().get_param(
            'website.portal_access_scope')
        self.assertEqual(value, 'portal')
