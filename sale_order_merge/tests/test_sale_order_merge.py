###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestSaleOrderMerge(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.product_model = self.env['product.product']
        self.sale_model = self.env['sale.order']
        self.sale_line_model = self.env['sale.order.line']
        self.pricelist_model = self.env['product.pricelist']
        self.wiz_model = self.env['sale.order.merge']
        self.partner_01 = self.partner_model.create({
            'name': 'Partner Test 01',
        })
        self.partner_01_invoice_a = self.env['res.partner'].create({
            'name': 'Partner 01 Invoice Address A',
            'parent_id': self.partner_01.id,
            'type': 'invoice',
        })
        self.partner_01_invoice_b = self.env['res.partner'].create({
            'name': 'Partner 01 Invoice Address B',
            'parent_id': self.partner_01.id,
            'type': 'invoice',
        })
        self.partner_01_shipping_a = self.env['res.partner'].create({
            'name': 'Partner 01 Shipping Address A',
            'parent_id': self.partner_01.id,
            'type': 'delivery',
        })
        self.partner_01_shipping_b = self.env['res.partner'].create({
            'name': 'Partner 01 Shipping Address B',
            'parent_id': self.partner_01.id,
            'type': 'delivery',
        })
        self.partner_02 = self.partner_model.create({
            'name': 'Partner Test 02',
        })
        self.product_01 = self.product_model.create({
            'type': 'service',
            'company_id': False,
            'name': 'Service Product 01',
            'standard_price': 10,
            'list_price': 20,
        })
        self.product_02 = self.product_model.create({
            'type': 'service',
            'company_id': False,
            'name': 'Service Product 02',
            'standard_price': 25,
            'list_price': 50,
        })
        self.product_03 = self.product_model.create({
            'type': 'service',
            'company_id': False,
            'name': 'Service Product 03',
            'standard_price': 50,
            'list_price': 100,
        })
        self.pricelist_01 = self.pricelist_model.create({
            'name': 'Test Pricelist 01',
            'currency_id': self.env.ref('base.EUR').id,
        })
        self.pricelist_02 = self.pricelist_model.create({
            'name': 'Test Pricelist 02',
            'currency_id': self.env.ref('base.EUR').id,
        })

    def create_sale_order(
            self, partner, product, partner_invoice=None,
            partner_shipping=None, client_order_ref=None,
            pricelist=None, origin=None):
        partner_invoice = partner_invoice or partner
        partner_shipping = partner_shipping or partner
        order = self.sale_model.create({
            'partner_id': partner.id,
            'partner_invoice_id': partner_invoice.id,
            'partner_shipping_id': partner_shipping.id,
            'client_order_ref': client_order_ref,
            'origin': origin,
            'pricelist_id': (
                pricelist and pricelist.id or self.pricelist_01.id),
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': product.list_price,
                    'product_uom_qty': 1,
                }),
            ],
        })
        return order

    def test_error_merge_one_order(self):
        sale = self.create_sale_order(
            self.partner_01, self.product_01)
        wizard = self.wiz_model.with_context({
            'active_ids': sale.ids,
        }).create({})
        with self.assertRaises(exceptions.UserError) as result:
            wizard.action_merge()
        self.assertEqual(
            str(result.exception),
            'You must select more than one order')

    def test_error_merge_orders_not_draft(self):
        sale_01 = self.create_sale_order(
            self.partner_01, self.product_01)
        sale_01.action_confirm()
        sale_02 = self.create_sale_order(
            self.partner_01, self.product_01)
        wizard = self.wiz_model.with_context({
            'active_ids': [
                sale_01.id,
                sale_02.id,
            ],
        }).create({})
        with self.assertRaises(exceptions.UserError) as result:
            wizard.action_merge()
        self.assertEqual(
            str(result.exception),
            'You must select orders in draft state')

    def test_error_merge_orders_different_partners(self):
        sale_01 = self.create_sale_order(
            self.partner_01, self.product_01)
        sale_02 = self.create_sale_order(
            self.partner_02, self.product_01)
        wizard = self.wiz_model.with_context({
            'active_ids': [
                sale_01.id,
                sale_02.id,
            ],
        }).create({})
        with self.assertRaises(exceptions.UserError) as result:
            wizard.action_merge()
        self.assertEqual(
            str(result.exception),
            'You can only merge orders from the same customer')

    def test_error_merge_orders_different_invoice_address(self):
        sale_01 = self.create_sale_order(
            self.partner_01, self.product_01,
            partner_invoice=self.partner_01_invoice_a)
        sale_02 = self.create_sale_order(
            self.partner_01, self.product_01,
            partner_invoice=self.partner_01_invoice_b)
        wizard = self.wiz_model.with_context({
            'active_ids': [
                sale_01.id,
                sale_02.id,
            ],
        }).create({})
        with self.assertRaises(exceptions.UserError) as result:
            wizard.action_merge()
        self.assertEqual(
            str(result.exception),
            'You can only merge orders with the same invoicing address')

    def test_error_merge_orders_different_shipping_address(self):
        sale_01 = self.create_sale_order(
            self.partner_01, self.product_01,
            partner_shipping=self.partner_01_shipping_a)
        sale_02 = self.create_sale_order(
            self.partner_01, self.product_01,
            partner_shipping=self.partner_01_shipping_b)
        wizard = self.wiz_model.with_context({
            'active_ids': [
                sale_01.id,
                sale_02.id,
            ],
        }).create({})
        with self.assertRaises(exceptions.UserError) as result:
            wizard.action_merge()
        self.assertEqual(
            str(result.exception),
            'You can only merge orders with the same shipping address')

    def test_error_merge_orders_different_pricelists(self):
        sale_01 = self.create_sale_order(
            self.partner_01, self.product_01)
        sale_02 = self.create_sale_order(
            self.partner_01, self.product_01, pricelist=self.pricelist_02)
        wizard = self.wiz_model.with_context({
            'active_ids': [
                sale_01.id,
                sale_02.id,
            ],
        }).create({})
        with self.assertRaises(exceptions.UserError) as result:
            wizard.action_merge()
        self.assertEqual(
            str(result.exception),
            'You can only merge orders with the same pricelist')

    def test_new_order_is_correct(self):
        sale_01 = self.create_sale_order(
            self.partner_01, self.product_01, client_order_ref='RefA',
            origin='SO001')
        sale_02 = self.create_sale_order(
            self.partner_01, self.product_02, client_order_ref='RefA',
            origin='SO002')
        sale_03 = self.create_sale_order(
            self.partner_01, self.product_03, client_order_ref='RefB',
            origin='SO003')
        additional_line = self.sale_line_model.new({
            'order_id': sale_03.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 1,
            'price_unit': 49.99,
        })
        additional_line.create(
            additional_line._convert_to_write(additional_line._cache))
        wizard = self.wiz_model.with_context({
            'active_ids': [
                sale_01.id,
                sale_02.id,
                sale_03.id,
            ],
        }).create({})
        result = wizard.action_merge()
        new_order = self.env['sale.order'].browse(result['res_id'])
        self.assertEqual(len(new_order.order_line), 4)
        self.assertEqual(new_order.origin, 'SO001, SO002, SO003')
        self.assertIn('RefA', new_order.client_order_ref)
        self.assertIn('RefB', new_order.client_order_ref)
        self.assertEqual(new_order.partner_id, self.partner_01)
        self.assertEqual(new_order.partner_invoice_id, self.partner_01)
        self.assertEqual(new_order.partner_shipping_id, self.partner_01)
        self.assertEqual(new_order.pricelist_id, self.pricelist_01)
        self.assertEqual(len(new_order.message_ids), 2)
        self.assertIn(
            'sales order has been created', new_order.message_ids[0].body)
        self.assertEqual(sale_01.state, 'draft')
        self.assertIn('has been merged in', sale_01.message_ids[0].body)
        self.assertEqual(sale_02.state, 'draft')
        self.assertIn('has been merged in', sale_02.message_ids[0].body)
        self.assertEqual(sale_03.state, 'draft')
        self.assertIn('has been merged in', sale_03.message_ids[0].body)
