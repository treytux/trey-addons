###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSaleRestrictPriceChange(TransactionCase):
    def setUp(self):
        super().setUp()
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'company_ids': [(6, 0, [self.env.user.company_id.id])],
            'company_id': self.env.user.company_id.id,
            'groups_id': [(6, 0, [
                self.env.ref('sales_team.group_sale_salesman_all_leads').id,
            ])],
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Test product 1',
            'list_price': 15,
            'standard_price': 4,
        })
        self.customer = self.env['res.partner'].create({
            'name': 'Test customer',
            'email': 'customer@customer.com',
            'customer': True,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1}),
            ]
        })

    def test_sale_restrict_price_change(self):
        line = self.sale.order_line[0]
        with self.assertRaises(UserError) as result:
            line.sudo(self.test_user.id).onchange_price_unit()
        self.assertEqual(
            'You do not have permissions to change the price.',
            result.exception.name)
        self.test_user.groups_id += self.env.ref(
            'sale_restrict_price_change.group_allow_change_price')
        line.sudo(self.test_user.id).onchange_price_unit()
