###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import TransactionCase


class TestSaleOrderPartnerShippingEmpty(TransactionCase):

    def setUp(self):
        super(TestSaleOrderPartnerShippingEmpty, self).setUp()
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser',
            'email': 'test@example.com',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('sales_team.group_sale_salesman').id,
            ])],
        })

    def test_shipping_address_empty(self):
        partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'company_type': 'company',
            'street': '123 Main Street',
            'city': 'Springfield',
            'child_ids': [(0, 0, {
                'name': 'Shipping Address',
                'type': 'delivery',
                'street': '456 Shipping Avenue',
                'city': 'Springfield',
            })]
        })
        group = (
            'sale_order_partner_shipping_empty.group_sale_no_default_shipping')
        self.user.write({
            'groups_id': [(4, self.env.ref(group).id)]
        })
        self.assertTrue(self.user.has_group(group))
        sale_order = self.env['sale.order'].sudo(self.user).new({
            'partner_id': partner.id,
        })
        sale_order.onchange_partner_id()
        self.assertFalse(sale_order.partner_shipping_id)

    def test_shipping_address_not_empty(self):
        partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'company_type': 'company',
            'street': '123 Main Street',
            'city': 'Springfield',
            'child_ids': [(0, 0, {
                'name': 'Shipping Address',
                'type': 'delivery',
                'street': '456 Shipping Avenue',
                'city': 'Springfield',
            })]
        })
        group = (
            'sale_order_partner_shipping_empty.group_sale_no_default_shipping')
        self.assertFalse(self.user.has_group(group))
        sale_order = self.env['sale.order'].sudo(self.user).new({
            'partner_id': partner.id,
        })
        sale_order.onchange_partner_id()
        self.assertTrue(sale_order.partner_shipping_id)
