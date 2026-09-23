###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import common


class TestResPartnerCreation(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_fail_create_partner(self):
        """ This test will fail because the user is not in the group """
        group = self.env.ref('partner_creation_acl.group_partner_creation')
        self.env.user.groups_id = [(3, group.id)]
        with self.assertRaises(ValidationError):
            self.partner = self.env['res.partner'].create({
                'name': 'Test Partner',
            })

    def test_create_partner(self):
        """ This test will not fail because the user is not in the group """
        group = self.env.ref('partner_creation_acl.group_partner_creation')
        self.env.user.groups_id = [(4, group.id)]
        self.assertTrue(group in self.env.user.groups_id)
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner2',
        })
