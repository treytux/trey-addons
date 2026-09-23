###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestReadOnlyField(TransactionCase):

    def setUp(self):
        super().setUp()
        self.user_demo = self.env['res.users'].create({
            'name': 'Test User Demo',
            'login': 'user@test.com',
            'company_id': self.env.ref('base.main_company').id,
            'groups_id': [(6, 0, [
                self.env.ref('sales_team.group_sale_manager').id,
            ])],
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'order_line': [(0, 0, {
                'product_id': self.env.ref('product.product_product_4').id,
                'product_uom_qty': 1,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
            })]
        })

    def test_field_is_readonly(self):
        order = self.sale.with_user(self.user_demo)
        self.assertFalse(order.has_group_readonly)
        readonly_group = self.env.ref(
            'sale_order_group_restrict_edit.group_sale_order_restriction')
        self.user_demo.write({
            'groups_id': [(4, readonly_group.id)],
        })
        order._compute_is_readonly()
        self.assertTrue(order.has_group_readonly)
