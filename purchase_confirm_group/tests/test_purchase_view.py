###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import TransactionCase


class TestPurchaseView(TransactionCase):

    def setUp(self):
        super().setUp()
        self.restricted_user = self.env['res.users'].create({
            'name': 'Restricted User',
            'login': 'restricted_user',
            'groups_id': [(6, 0, [
                self.env.ref('purchase.group_purchase_user').id
            ])],
        })
        self.authorised_user = self.env['res.users'].create({
            'name': 'Authorised User',
            'login': 'authorised_user',
            'groups_id': [(6, 0, [
                self.env.ref('purchase.group_purchase_user').id,
                self.env.ref(
                    'purchase_confirm_group.allow_purchase_confirm_group').id
            ])],
        })

    def test_button_visibility(self):
        view = 'purchase.purchase_order_form'
        view_restricted = self.env['purchase.order'].with_user(
            self.restricted_user).get_view(view_id=self.env.ref(view).id)
        self.assertNotIn('id="draft_confirm"', view_restricted['arch'])
        view_authorised = self.env['purchase.order'].with_user(
            self.authorised_user).get_view(view_id=self.env.ref(view).id)
        self.assertIn('id="draft_confirm"', view_authorised['arch'])
