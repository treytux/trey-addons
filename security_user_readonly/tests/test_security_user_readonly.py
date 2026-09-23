###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import AccessError
from odoo.tests.common import HttpCase, TransactionCase


class TestSecurityUserReadonly(TransactionCase):

    def setUp(self):
        super().setUp()

    def test_user_readonly(self):
        user = self.env.ref('base.user_admin')
        user.groups_id = [
            (4, self.ref('security_user_readonly.group_user_readonly')),
        ]
        partner = self.env.ref('base.res_partner_1').sudo(user)
        with self.assertRaises(AccessError) as exception:
            partner.write({'name': 'test'})
        self.assertIn(
            'Your user has read-only permissions', str(exception.exception))
        with self.assertRaises(AccessError) as exception:
            partner.create({'name': 'test'})
        self.assertIn(
            'Your user has read-only permissions', str(exception.exception))
        with self.assertRaises(AccessError) as exception:
            partner.unlink()
        self.assertIn(
            'Your user has read-only permissions', str(exception.exception))
        user.groups_id = [
            (3, self.ref('security_user_readonly.group_user_readonly')),
        ]
        partner.write({'name': 'test'})
        new_partner = partner.create({'name': 'test'}).sudo(user)
        new_partner.unlink()


class TestSecurityUserReadonlyAuthenticate(HttpCase):

    def setUp(self):
        super().setUp()

    def test_user_readonly_authenticate(self):
        user = self.env.ref('base.user_admin')
        user.groups_id = [
            (4, self.ref('security_user_readonly.group_user_readonly')),
        ]
        self.authenticate('admin', 'admin')
