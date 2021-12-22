###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderPartnerGroup(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_1 = self.env['res.partner'].create({
            'name': 'Test partner 1',
            'is_company': True,
        })
        self.partner_2 = self.env['res.partner'].create({
            'name': 'Test partner 2',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Consumible product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.partner_group_1 = self.env['res.partner'].create({
            'name': 'Test partner group 1',
            'is_company': False,
        })
        self.partner_group_2 = self.env['res.partner'].create({
            'name': 'Test partner group 2',
            'is_company': False,
        })

    def test_create_sale_order_and_add_partner(self):
        self.assertFalse(self.partner_1.partner_group_id)
        self.partner_1.write({
            'partner_group_id': self.partner_group_1.id,
        })
        self.assertEqual(
            self.partner_1.partner_group_id.id, self.partner_group_1.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        sale.onchange_partner_id()
        self.assertEqual(
            sale.partner_group_id.id, self.partner_1.partner_group_id.id)
        self.assertFalse(self.partner_2.partner_group_id)
        self.partner_2.write({
            'partner_group_id': self.partner_group_2.id,
        })
        self.assertEqual(
            self.partner_2.partner_group_id.id, self.partner_group_2.id)
        sale.write({
            'partner_id': self.partner_2.id,
        })
        sale.onchange_partner_id()
        self.assertNotEqual(
            sale.partner_group_id, self.partner_1.partner_group_id)
        self.assertEqual(
            sale.partner_group_id, self.partner_2.partner_group_id)

    def test_create_multiple_sale_order_and_change_partner_group_id(self):
        self.assertFalse(self.partner_1.partner_group_id)
        self.partner_1.write({
            'partner_group_id': self.partner_group_1.id,
        })
        self.assertEqual(
            self.partner_1.partner_group_id.id, self.partner_group_1.id)
        sale_1 = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        sale_1.onchange_partner_id()
        self.assertEqual(
            sale_1.partner_group_id.id, self.partner_1.partner_group_id.id)
        sale_1.action_confirm()
        self.partner_1.write({
            'partner_group_id': self.partner_group_2.id,
        })
        self.assertEqual(
            sale_1.partner_group_id, self.partner_group_1)
        self.assertNotEqual(
            self.partner_1.partner_group_id, self.partner_group_1)
        self.assertEqual(
            self.partner_1.partner_group_id, self.partner_group_2)
        sale_2 = self.env['sale.order'].create({
            'partner_id': self.partner_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        sale_2.onchange_partner_id()
        self.assertEqual(
            sale_2.partner_group_id, self.partner_1.partner_group_id)
        sale_2.action_confirm()
