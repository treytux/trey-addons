###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from lxml import etree, html
from odoo.tests.common import TransactionCase


class TestIrUiViewRestrictedGroups(TransactionCase):

    def setUp(self):
        super().setUp()
        self.user_demo = self.env.ref('base.user_demo')
        self.user_admin = self.env.ref('base.user_admin')
        self.group = self.env.ref('base.group_system')

    def test_view_restricted_group(self):
        partner_view = self.env.ref('base.view_partner_form')
        new_partner_view = partner_view.copy()
        new_partner_view.priority = 2
        ref_field = new_partner_view.arch.find('field name="ref"')
        self.assertNotEqual(ref_field, -1)
        tree = html.fromstring(new_partner_view.arch)
        xpath = tree.xpath('//field[@name="ref"]')
        elem = xpath[0]
        parent = elem.getparent()
        parent.remove(elem)
        new_partner_view.arch = etree.tostring(tree, pretty_print=True)
        ref_field = new_partner_view.arch.find('field name="ref"')
        self.assertEqual(ref_field, -1)
        new_partner_view.name = 'Custom partner form view test'
        self.assertTrue(new_partner_view)
        self.assertTrue(self.group in self.user_admin.groups_id)
        self.assertTrue(self.group not in self.user_demo.groups_id)
        partner_view.groups_id = [(6, 0, [self.group.id])]
        view_03 = self.env['res.partner'].with_user(self.user_admin).get_view()
        self.assertIn('<field name="ref"', view_03['arch'])
        view_04 = self.env['res.partner'].with_user(self.user_demo).get_view()
        self.assertNotIn('<field name="ref"', view_04['arch'])
