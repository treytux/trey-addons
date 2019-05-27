###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPartnerBlocking(TransactionCase):

    def setUp(self):
        super().setUp()
        self.parent = self.env.ref('partner_blocking.partner_parent')
        self.child_1 = self.env.ref('partner_blocking.partner_child_1')
        self.child_2 = self.env.ref('partner_blocking.partner_child_2')
        self.user = self.env.ref('partner_blocking.user')
        self.user.partner_id.parent_id = self.parent
        self.parent.message_post('Message Test')

    def is_all_allowed(self):
        self.assertTrue(self.parent.allowed)
        self.assertTrue(self.child_1.allowed)
        self.assertTrue(self.child_2.allowed)
        self.assertTrue(self.user.allowed)

    def has_message(self, partner, change_from):
        return bool([
            m for m in partner.message_ids
            if self.parent._allowed_message_get(change_from) in m.body])

    def test_blocked_partner(self):
        self.parent.toggle_allowed()
        self.assertFalse(self.parent.allowed)
        self.assertFalse(self.child_1.allowed)
        self.assertFalse(self.child_2.allowed)
        self.assertFalse(self.user.allowed)
        self.assertEquals(len(self.parent.message_ids), 3)
        self.assertTrue(self.has_message(self.parent, 'partner'))
        self.assertTrue(self.has_message(self.child_1, 'parent'))
        self.assertTrue(self.has_message(self.child_2, 'parent'))
        self.assertTrue(self.has_message(self.user.partner_id, 'parent'))

    def test_blocked_child(self):
        self.is_all_allowed()
        self.child_1.toggle_allowed()
        self.assertFalse(self.parent.allowed)
        self.assertFalse(self.child_1.allowed)
        self.assertFalse(self.child_2.allowed)
        self.assertFalse(self.user.allowed)
        self.assertEquals(len(self.parent.message_ids), 3)
        self.assertTrue(self.has_message(self.parent, 'child'))
        self.assertTrue(self.has_message(self.child_1, 'partner'))
        self.assertTrue(self.has_message(self.child_2, 'parent'))
        self.assertTrue(self.has_message(self.user.partner_id, 'parent'))

    def test_blocked_user(self):
        self.is_all_allowed()
        self.user.toggle_allowed()
        self.assertFalse(self.parent.allowed)
        self.assertFalse(self.child_1.allowed)
        self.assertFalse(self.child_2.allowed)
        self.assertFalse(self.user.allowed)
        self.assertEquals(len(self.parent.message_ids), 3)
        self.assertTrue(self.has_message(self.parent, 'child'))
        self.assertTrue(self.has_message(self.child_1, 'parent'))
        self.assertTrue(self.has_message(self.child_2, 'parent'))
        self.assertTrue(self.has_message(self.user.partner_id, 'user'))
