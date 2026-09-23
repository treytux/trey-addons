###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestStockPickingInvoiceCarrier(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.carrier_partner = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test product',
            'type': 'product',
            'default_code': 'PR-TEST',
            'standard_price': 10,
            'list_price': 35,
        })
        self.product_delivery = self.env['product.product'].create({
            'type': 'service',
            'name': 'Product delivery test',
            'standard_price': 2.99,
            'list_price': 2.99,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'delivery_type': 'fixed',
            'product_id': self.product_delivery.id,
            'fixed_price': 2.99,
            'partner_id': self.carrier_partner.id,
        })
        self.sale_01 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'carrier_id': self.carrier.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 45,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.sale_02 = self.sale_01.copy()
        self.sale_03 = self.sale_01.copy()
        self.location = self.env.ref('stock.stock_location_stock')

    def inventory(self, location, qty):
        inventory = self.env['stock.inventory'].create({
            'name': 'add products for tests',
            'filter': 'product',
            'location_id': location.id,
            'product_id': self.product.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.write({
            'product_qty': qty,
            'location_id': location.id,
        })
        inventory._action_done()

    def test_invoice_pickings_carrier_01(self):
        self.assertEqual(self.sale_01.carrier_id, self.carrier)
        self.assertEqual(self.sale_02.carrier_id, self.carrier)
        self.assertEqual(self.sale_03.carrier_id, self.carrier)
        self.inventory(self.location, 10)
        self.sale_01.action_confirm()
        self.sale_02.action_confirm()
        self.sale_03.action_confirm()
        self.assertEqual(len(self.sale_01.picking_ids), 1)
        self.assertEqual(len(self.sale_02.picking_ids), 1)
        self.assertEqual(len(self.sale_03.picking_ids), 1)
        picking_01 = self.sale_01.picking_ids[0]
        picking_02 = self.sale_02.picking_ids[0]
        picking_03 = self.sale_03.picking_ids[0]
        wizard = self.env['stock.picking.invoice_carrier'].with_context(
            active_model='stock.picking',
            active_ids=[picking_01.id, picking_02.id, picking_03.id],
        ).create({})
        invoices = wizard.button_accept()
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0].partner_id, self.carrier.partner_id)
        self.assertEqual(len(invoices[0].invoice_line_ids), 3)
        self.assertIn(picking_01.name, invoices[0].invoice_line_ids[0].name)
        self.assertIn(picking_02.name, invoices[0].invoice_line_ids[1].name)
        self.assertIn(picking_03.name, invoices[0].invoice_line_ids[2].name)
        self.assertEqual(
            invoices[0].amount_untaxed,
            self.product_delivery.standard_price * 3)

    def test_invoice_pickings_carrier_02(self):
        self.assertEqual(self.sale_01.carrier_id, self.carrier)
        self.assertEqual(self.sale_02.carrier_id, self.carrier)
        self.assertEqual(self.sale_03.carrier_id, self.carrier)
        carrier_partner_02 = self.env['res.partner'].create({
            'name': 'Carrier partner 2',
        })
        carrier_02 = self.env['delivery.carrier'].create({
            'name': 'Carrier test 2',
            'delivery_type': 'fixed',
            'product_id': self.product_delivery.id,
            'fixed_price': 4.99,
            'partner_id': carrier_partner_02.id,
        })
        self.sale_02.carrier_id = carrier_02.id
        self.sale_03.carrier_id = carrier_02.id
        self.assertEqual(self.sale_02.carrier_id, carrier_02)
        self.assertEqual(self.sale_03.carrier_id, carrier_02)
        self.inventory(self.location, 10)
        self.sale_01.action_confirm()
        self.sale_02.action_confirm()
        self.sale_03.action_confirm()
        self.assertEqual(len(self.sale_01.picking_ids), 1)
        self.assertEqual(len(self.sale_02.picking_ids), 1)
        self.assertEqual(len(self.sale_03.picking_ids), 1)
        picking_01 = self.sale_01.picking_ids[0]
        picking_02 = self.sale_02.picking_ids[0]
        picking_03 = self.sale_03.picking_ids[0]
        wizard = self.env['stock.picking.invoice_carrier'].with_context(
            active_model='stock.picking',
            active_ids=[picking_01.id, picking_02.id, picking_03.id],
        ).create({})
        invoices = wizard.button_accept()
        self.assertEqual(len(invoices), 2)
        self.assertEqual(picking_01.invoice_carrier_id, invoices[0])
        self.assertEqual(picking_02.invoice_carrier_id, invoices[1])
        self.assertEqual(picking_03.invoice_carrier_id, invoices[1])
        self.assertEqual(invoices[0].partner_id, self.carrier.partner_id)
        self.assertEqual(invoices[1].partner_id, carrier_02.partner_id)
        self.assertEqual(len(invoices[0].invoice_line_ids), 1)
        self.assertEqual(len(invoices[1].invoice_line_ids), 2)
        self.assertIn(picking_01.name, invoices[0].invoice_line_ids[0].name)
        self.assertEqual(invoices[0].invoice_line_ids[0].picking_id, picking_01)
        self.assertIn(picking_02.name, invoices[1].invoice_line_ids[0].name)
        self.assertEqual(invoices[1].invoice_line_ids[0].picking_id, picking_02)
        self.assertIn(picking_03.name, invoices[1].invoice_line_ids[1].name)
        self.assertEqual(invoices[1].invoice_line_ids[1].picking_id, picking_03)
        self.assertEqual(
            invoices[0].amount_untaxed, self.product_delivery.standard_price)
        self.assertEqual(
            invoices[1].amount_untaxed,
            self.product_delivery.standard_price * 2)

    def test_invoice_pickings_carrier_without_partner(self):
        self.assertEqual(self.sale_01.carrier_id, self.carrier)
        self.assertEqual(self.sale_02.carrier_id, self.carrier)
        self.assertEqual(self.sale_03.carrier_id, self.carrier)
        self.assertEqual(self.carrier.partner_id, self.carrier_partner)
        self.carrier.partner_id = False
        self.assertFalse(self.carrier.partner_id)
        self.inventory(self.location, 10)
        self.sale_01.action_confirm()
        self.sale_02.action_confirm()
        self.sale_03.action_confirm()
        self.assertEqual(len(self.sale_01.picking_ids), 1)
        self.assertEqual(len(self.sale_02.picking_ids), 1)
        self.assertEqual(len(self.sale_03.picking_ids), 1)
        picking_01 = self.sale_01.picking_ids[0]
        picking_02 = self.sale_02.picking_ids[0]
        picking_03 = self.sale_03.picking_ids[0]
        wizard = self.env['stock.picking.invoice_carrier'].with_context(
            active_model='stock.picking',
            active_ids=[picking_01.id, picking_02.id, picking_03.id],
        ).create({})
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.button_accept()
        self.assertIn('must have an assigned partner', result.exception.name)
