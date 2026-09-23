###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAliasDomain(TransactionCase):

    def setUp(self):
        super(TestAliasDomain, self).setUp()
        self.company_01 = self.env.ref('base.main_company')
        self.company_02 = self.env['res.company'].create({
            'name': '2nd Company',
            'alias_domain': 'company02.example.com'
        })

    def test_alias_domain_different_companies(self):
        self.assertNotEqual(
            self.company_01.alias_domain, self.company_02.alias_domain)
        self.assertFalse(self.company_01.alias_domain)
        self.assertEqual(self.company_02.alias_domain, 'company02.example.com')

    def test_change_alias_domain(self):
        self.company_01.alias_domain = 'newdom.company01.com'
        self.assertEqual(self.company_01.alias_domain, 'newdom.company01.com')

    def test_config_settings_changes_alias_domain(self):
        config = self.env['res.config.settings'].create({
            'alias_domain': 'config.company01.com',
        })
        config.set_values()
        self.assertEqual(self.company_01.alias_domain, 'config.company01.com')

    def test_get_values_config_settings(self):
        self.env.user.company_id = self.company_02
        config = self.env['res.config.settings'].create({})
        values = config.get_values()
        self.assertEqual(values['alias_domain'], self.company_02.alias_domain)
