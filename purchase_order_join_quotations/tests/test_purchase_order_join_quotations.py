###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPurchaseOrderJoinQuotations(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test 1',
        })
        self.partner2 = self.env['res.partner'].create({
            'name': 'Partner test 2',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product2 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product2',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product3 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product3',
            'standard_price': 10,
            'list_price': 100,
        })

    def test_error_join_one_quotation(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line = self.env['purchase.order.line'].new({
            'order_id': purchase.id,
            'product_id': self.product.id,
            'product_qty': 1,
            'price_unit': 99.99,
        })
        line.onchange_product_id()
        line.create(line._convert_to_write(line._cache))
        wizard = self.env['purchase.order.join'].with_context({
            'active_ids': purchase.ids,
        }).create({})
        with self.assertRaises(Exception):
            wizard.action_join()

    def test_error_join_quotations_not_draft(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line = self.env['purchase.order.line'].new({
            'order_id': purchase.id,
            'product_id': self.product.id,
            'product_qty': 1,
            'price_unit': 99.99,
        })
        line.onchange_product_id()
        line.create(line._convert_to_write(line._cache))
        purchase.button_confirm()
        purchase2 = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line2 = self.env['purchase.order.line'].new({
            'order_id': purchase2.id,
            'product_id': self.product.id,
            'product_qty': 1,
            'price_unit': 99.99,
        })
        line2.onchange_product_id()
        line2.create(line2._convert_to_write(line2._cache))
        wizard = self.env['purchase.order.join'].with_context({
            'active_ids': [
                purchase.id,
                purchase2.id,
            ],
        }).create({})
        with self.assertRaises(Exception):
            wizard.action_join()

    def test_error_join_quotations_different_partners(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line = self.env['purchase.order.line'].new({
            'order_id': purchase.id,
            'product_id': self.product.id,
            'product_qty': 1,
            'price_unit': 99.99,
        })
        line.onchange_product_id()
        line.create(line._convert_to_write(line._cache))
        purchase2 = self.env['purchase.order'].create({
            'partner_id': self.partner2.id,
        })
        line2 = self.env['purchase.order.line'].new({
            'order_id': purchase2.id,
            'product_id': self.product.id,
            'product_qty': 1,
            'price_unit': 99.99,
        })
        line2.onchange_product_id()
        line2.create(line2._convert_to_write(line2._cache))
        wizard = self.env['purchase.order.join'].with_context({
            'active_ids': [
                purchase.id,
                purchase2.id,
            ],
        }).create({})
        with self.assertRaises(Exception):
            wizard.action_join()

    def test_join_quotations_correct_origin(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'origin': 'PO001',
        })
        origin_purchase = purchase.origin
        line = self.env['purchase.order.line'].new({
            'order_id': purchase.id,
            'product_id': self.product.id,
            'product_qty': 1,
            'price_unit': 99.99,
        })
        line.onchange_product_id()
        line_qty = line.product_qty
        line.create(line._convert_to_write(line._cache))
        line_name = line.name
        purchase2 = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'origin': 'PO002',
        })
        origin_purchase2 = purchase2.origin
        line2 = self.env['purchase.order.line'].new({
            'order_id': purchase2.id,
            'product_id': self.product2.id,
            'product_qty': 1,
            'price_unit': 99.99,
        })
        line2.onchange_product_id()
        line2_qty = line2.product_qty
        line2.create(line2._convert_to_write(line2._cache))
        line2_name = line2.name
        purchase3 = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'origin': 'PO003',
        })
        origin_purchase3 = purchase3.origin
        line3 = self.env['purchase.order.line'].new({
            'order_id': purchase3.id,
            'product_id': self.product3.id,
            'product_qty': 1,
            'price_unit': 99.99,
        })
        line3.onchange_product_id()
        line3_qty = line3.product_qty
        line3.create(line3._convert_to_write(line3._cache))
        line3_name = line3.name
        wizard = self.env['purchase.order.join'].with_context({
            'active_ids': [
                purchase.id,
                purchase2.id,
                purchase3.id,
            ],
        }).create({})
        wizard.action_join()
        line_product = purchase.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEquals(line_name, line_product.name)
        self.assertEquals(line_qty, line_product.product_qty)
        line_product2 = purchase.order_line.filtered(
            lambda ln: ln.product_id == self.product2)
        self.assertEquals(line2_name, line_product2.name)
        self.assertEquals(line2_qty, line_product2.product_qty)
        line_product3 = purchase.order_line.filtered(
            lambda ln: ln.product_id == self.product3)
        self.assertEquals(line3_name, line_product3.name)
        self.assertEquals(line3_qty, line_product3.product_qty)
        self.assertIn(origin_purchase, purchase.origin)
        self.assertIn(origin_purchase2, purchase.origin)
        self.assertIn(origin_purchase3, purchase.origin)
        self.assertFalse(purchase2.exists())
        self.assertFalse(purchase3.exists())
