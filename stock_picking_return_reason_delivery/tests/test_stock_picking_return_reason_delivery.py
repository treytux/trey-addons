###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestStockPickingReturnReasonDelivery(common.TransactionCase):

    def setUp(self):
        super().setUp()
        spain_country = self.env.ref('base.es')
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'country_id': spain_country.id,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 25,
            'invoice_policy': 'delivery',
        })
        self.product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
            'type': 'service',
        })
        self.carrier_test_es = self.env['delivery.carrier'].create({
            'name': 'Carrier test send Spain',
            'delivery_type': 'fixed',
            'product_id': self.product_carrier.id,
            'fixed_price': 3.99,
            'country_ids': [(6, 0, spain_country.ids)],
        })
        self.journal_sale = self.env['account.journal'].create({
            'name': 'Test journal sale',
            'code': 'TST-JRNL-S',
            'type': 'sale',
            'company_id': self.env.ref('base.main_company').id,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 2,
                    'price_unit': 25,
                }),
            ],
        })
        self.reason = self.env['stock.picking.return.reason'].create({
            'name': 'Return reason test',
            'description': 'Summary of return reason test',
        })
        self.reason_carrier_es = (
            self.env['stock.picking.return.reason'].create({
                'name': 'Return reason carrier Spain test',
                'description': 'Summary of return reason carrier Spain test',
                'carrier_id': self.carrier_test_es.id,
            })
        )
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.stock_wh.lot_stock_id.return_location = True

    def get_stock(self, product, location):
        return product.with_context(location=location.id).qty_available

    def update_stock(self, product, location, qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'new_quantity': qty,
        })
        wizard.change_product_qty()
        product_qty = self.get_stock(product, location)
        self.assertEqual(product_qty, qty)

    def picking_transfer(self, picking, qty):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = qty
        picking.button_validate()

    def test_return_with_reason_without_carrier_inv_policy_delivery(self):
        self.assertEqual(self.reason.pickings_count, 0)
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.return_reason_id)
        self.picking_transfer(picking, 2)
        self.assertEqual(picking.state, 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_id=picking.id,
            active_ids=picking.ids,
            active_model='stock.picking'
        ).create({})
        return_picking._onchange_picking_id()
        self.assertFalse(return_picking.return_reason_id)
        self.assertTrue(return_picking.location_id)
        return_picking.return_reason_id = self.reason.id
        self.assertEqual(return_picking.return_reason_id, self.reason)
        return_picking.product_return_moves.write({
            'quantity': 2,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 2)
        picking_ret = self.sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        self.assertEqual(picking.return_reason_id, self.reason)
        self.assertEqual(self.reason.pickings_count, 1)
        self.assertEqual(len(self.reason.picking_ids), 1)
        self.assertEqual(self.reason.picking_ids[0], picking)
        sale_02 = self.sale.copy()
        self.assertEqual(sale_02.state, 'draft')
        sale_02.action_confirm()
        picking_02 = sale_02.picking_ids[0]
        self.assertFalse(picking_02.return_reason_id)
        self.picking_transfer(picking_02, 2)
        self.assertEqual(picking_02.state, 'done')
        return_picking_02 = self.env['stock.return.picking'].with_context(
            active_id=picking_02.id,
            active_ids=picking_02.ids,
            active_model='stock.picking'
        ).create({})
        return_picking_02._onchange_picking_id()
        self.assertFalse(return_picking_02.return_reason_id)
        return_picking_02.return_reason_id = self.reason.id
        self.assertEqual(return_picking_02.return_reason_id, self.reason)
        return_picking_02.product_return_moves.write({
            'quantity': 2,
            'to_refund': True,
        })
        return_picking_02.create_returns()
        self.assertEqual(len(sale_02.picking_ids), 2)
        picking_ret_02 = sale_02.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret_02), 1)
        self.assertEqual(picking_02.return_reason_id, self.reason)
        self.assertEqual(self.reason.pickings_count, 2)
        self.assertEqual(len(self.reason.picking_ids), 2)
        picking_reason_01 = self.reason.picking_ids.filtered(
            lambda p: p.id == picking.id)
        self.assertEqual(len(picking_reason_01), 1)
        picking_reason_02 = self.reason.picking_ids.filtered(
            lambda p: p.id == picking_02.id)
        self.assertEqual(len(picking_reason_02), 1)

    def test_return_with_reason_without_carrier_invoices_inv_policy_delivery(
            self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.return_reason_id)
        self.picking_transfer(picking, 2)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(self.sale.order_line.qty_to_invoice, 2)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(self.sale)
        invoice = self.sale.invoice_ids[0]
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(self.sale.invoice_ids), 1)
        self.assertEqual(self.sale.invoice_ids, invoice)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(self.sale.order_line.qty_to_invoice, 0)
        self.assertEqual(len(self.sale.invoice_ids.invoice_line_ids), 1)
        self.assertEqual(
            self.sale.invoice_ids.invoice_line_ids.product_id, self.product)
        return_picking = self.env['stock.return.picking'].with_context(
            active_id=picking.id,
            active_ids=picking.ids,
            active_model='stock.picking'
        ).create({})
        return_picking._onchange_picking_id()
        self.assertFalse(return_picking.return_reason_id)
        return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 2)
        picking_ret = self.sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(picking_ret.state, 'done')
        self.assertEqual(self.sale.order_line.qty_delivered, 1)
        self.assertEqual(self.sale.order_line.qty_invoiced, 2)
        self.assertEqual(self.sale.order_line.qty_to_invoice, -1)
        invoice_ref = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(self.sale)
        self.assertEqual(len(self.sale.invoice_ids), 2)
        invoice_refund = self.sale.invoice_ids.filtered(
            lambda inv: inv.move_type == 'out_refund')
        self.assertEqual(len(invoice_refund), 1)
        self.assertEqual(invoice_refund, invoice_ref)
        self.assertEqual(self.sale.order_line.qty_delivered, 1)
        self.assertEqual(self.sale.order_line.qty_invoiced, 1)
        self.assertEqual(self.sale.order_line.qty_to_invoice, 0)

    def test_return_with_reason_with_carrier_invoice_inv_policy_delivery(self):
        self.reason.carrier_id = self.carrier_test_es.id
        self.assertEqual(self.reason.pickings_count, 0)
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.return_reason_id)
        self.picking_transfer(picking, 2)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(self.sale.order_line.qty_to_invoice, 2)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(self.sale)
        invoice = self.sale.invoice_ids[0]
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(self.sale.invoice_ids), 1)
        self.assertEqual(self.sale.invoice_ids, invoice)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(self.sale.order_line.qty_to_invoice, 0)
        self.assertEqual(len(self.sale.invoice_ids.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids.product_id, self.product)
        self.assertEqual(invoice.invoice_line_ids.quantity, 2)
        self.assertEqual(invoice.invoice_line_ids.price_unit, 25)
        self.assertEqual(invoice.amount_untaxed, 50)
        return_picking = self.env['stock.return.picking'].with_context(
            active_id=picking.id,
            active_ids=picking.ids,
            active_model='stock.picking'
        ).create({})
        return_picking._onchange_picking_id()
        self.assertFalse(return_picking.return_reason_id)
        return_picking.return_reason_id = self.reason.id
        self.assertEqual(
            return_picking.return_reason_id.carrier_id, self.carrier_test_es)
        return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 2)
        picking_ret = self.sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(picking_ret.state, 'done')
        self.assertEqual(len(self.sale.order_line), 2)
        delivery_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_carrier)
        self.assertEqual(len(delivery_line), 1)
        self.assertTrue(delivery_line.is_delivery_return)
        product_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(product_line), 1)
        self.assertEqual(product_line.qty_delivered, 1)
        self.assertEqual(product_line.qty_invoiced, 2)
        self.assertEqual(product_line.qty_to_invoice, -1)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(delivery_line.qty_invoiced, 0)
        self.assertEqual(delivery_line.qty_to_invoice, 1)
        invoice_ref = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(self.sale)
        self.assertEqual(len(self.sale.invoice_ids), 2)
        invoice_refund = self.sale.invoice_ids.filtered(
            lambda inv: inv.move_type == 'out_refund')
        self.assertEqual(len(invoice_refund), 1)
        self.assertEqual(invoice_refund, invoice_ref)
        self.assertEqual(len(invoice_refund.invoice_line_ids), 2)
        invoice_line_refund_product = invoice_refund.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(invoice_line_refund_product), 1)
        invoice_line_refund_carrier = invoice_refund.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_carrier)
        self.assertEqual(len(invoice_line_refund_carrier), 1)
        self.assertEqual(invoice_line_refund_product.quantity, 1)
        self.assertEqual(invoice_line_refund_product.price_unit, 25)
        self.assertEqual(invoice_line_refund_carrier.quantity, -1)
        self.assertEqual(invoice_line_refund_carrier.price_unit, 3.99)
        self.assertEqual(invoice_refund.amount_untaxed, 21.01)
        self.assertEqual(product_line.qty_delivered, 1)
        self.assertEqual(product_line.qty_invoiced, 1)
        self.assertEqual(product_line.qty_to_invoice, 0)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(delivery_line.qty_invoiced, 1)
        self.assertEqual(delivery_line.qty_to_invoice, 0)

    def test_return_with_reason_with_carrier_inv_two_ret_inv_policy_delivery(
            self):
        self.reason.carrier_id = self.carrier_test_es.id
        self.assertEqual(self.reason.pickings_count, 0)
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.return_reason_id)
        self.picking_transfer(picking, 2)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(self.sale.order_line.qty_to_invoice, 2)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(self.sale)
        invoice = self.sale.invoice_ids[0]
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(self.sale.invoice_ids), 1)
        self.assertEqual(self.sale.invoice_ids, invoice)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(self.sale.order_line.qty_to_invoice, 0)
        self.assertEqual(len(self.sale.invoice_ids.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids.product_id, self.product)
        self.assertEqual(invoice.invoice_line_ids.quantity, 2)
        self.assertEqual(invoice.invoice_line_ids.price_unit, 25)
        self.assertEqual(invoice.amount_untaxed, 50)
        return_picking = self.env['stock.return.picking'].with_context(
            active_id=picking.id,
            active_ids=picking.ids,
            active_model='stock.picking'
        ).create({})
        return_picking._onchange_picking_id()
        self.assertFalse(return_picking.return_reason_id)
        return_picking.return_reason_id = self.reason.id
        self.assertEqual(
            return_picking.return_reason_id.carrier_id, self.carrier_test_es)
        return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 2)
        picking_ret = self.sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(picking_ret.state, 'done')
        self.assertEqual(len(self.sale.order_line), 2)
        delivery_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_carrier)
        self.assertEqual(len(delivery_line), 1)
        self.assertTrue(delivery_line.is_delivery_return)
        product_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(product_line), 1)
        self.assertEqual(product_line.qty_delivered, 1)
        self.assertEqual(product_line.qty_invoiced, 2)
        self.assertEqual(product_line.qty_to_invoice, -1)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(delivery_line.qty_invoiced, 0)
        self.assertEqual(delivery_line.qty_to_invoice, 1)
        invoice_ref = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(self.sale)
        self.assertEqual(len(self.sale.invoice_ids), 2)
        invoice_refund = self.sale.invoice_ids.filtered(
            lambda inv: inv.move_type == 'out_refund')
        self.assertEqual(len(invoice_refund), 1)
        self.assertEqual(invoice_refund, invoice_ref)
        self.assertEqual(len(invoice_refund.invoice_line_ids), 2)
        invoice_line_refund_product = invoice_refund.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(invoice_line_refund_product), 1)
        invoice_line_refund_carrier = invoice_refund.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_carrier)
        self.assertEqual(len(invoice_line_refund_carrier), 1)
        self.assertEqual(invoice_line_refund_product.quantity, 1)
        self.assertEqual(invoice_line_refund_product.price_unit, 25)
        self.assertEqual(invoice_line_refund_carrier.quantity, -1)
        self.assertEqual(invoice_line_refund_carrier.price_unit, 3.99)
        self.assertEqual(invoice_refund.amount_untaxed, 21.01)
        self.assertEqual(product_line.qty_delivered, 1)
        self.assertEqual(product_line.qty_invoiced, 1)
        self.assertEqual(product_line.qty_to_invoice, 0)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(delivery_line.qty_invoiced, 1)
        self.assertEqual(delivery_line.qty_to_invoice, 0)
        return_return_picking = self.env['stock.return.picking'].with_context(
            active_id=picking_ret.id,
            active_ids=picking_ret.ids,
            active_model='stock.picking'
        ).create({})
        return_return_picking._onchange_picking_id()
        self.assertFalse(return_return_picking.return_reason_id)
        return_return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 3)
        picking_ret_ret = self.sale.picking_ids.filtered(
            lambda p: p.state == 'waiting')
        self.assertEqual(len(picking_ret_ret), 1)
        self.picking_transfer(picking_ret_ret, 1)
        self.assertEqual(picking_ret_ret.state, 'done')
        self.assertEqual(len(self.sale.order_line), 2)
        delivery_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_carrier)
        self.assertEqual(len(delivery_line), 1)
        self.assertTrue(delivery_line.is_delivery_return)
        product_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(product_line), 1)
        self.assertEqual(product_line.qty_delivered, 2)
        self.assertEqual(product_line.qty_invoiced, 1)
        self.assertEqual(product_line.qty_to_invoice, 1)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(delivery_line.qty_invoiced, 1)
        self.assertEqual(delivery_line.qty_to_invoice, 0)
        invoice_02 = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(self.sale)
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(self.sale.invoice_ids), 3)
        invoice2 = self.sale.invoice_ids.filtered(
            lambda inv: inv.move_type == 'out_invoice'
            and inv != invoice)
        self.assertEqual(len(invoice2), 1)
        self.assertEqual(invoice_02, invoice2)
        self.assertEqual(len(invoice_02.invoice_line_ids), 1)
        self.assertEqual(invoice_02.invoice_line_ids.product_id, self.product)
        self.assertEqual(invoice_02.invoice_line_ids.quantity, 1)
        self.assertEqual(invoice_02.invoice_line_ids.price_unit, 25)
        self.assertEqual(invoice_02.amount_untaxed, 25)
        self.assertEqual(product_line.qty_delivered, 2)
        self.assertEqual(product_line.qty_invoiced, 2)
        self.assertEqual(product_line.qty_to_invoice, 0)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(delivery_line.qty_invoiced, 1)
        self.assertEqual(delivery_line.qty_to_invoice, 0)

    def test_return_with_reason_with_carrier_inv_after_ret_inv_policy_delivery(
            self):
        self.reason.carrier_id = self.carrier_test_es.id
        self.assertEqual(self.reason.pickings_count, 0)
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.return_reason_id)
        self.picking_transfer(picking, 2)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(self.sale.order_line.qty_to_invoice, 2)
        return_picking = self.env['stock.return.picking'].with_context(
            active_id=picking.id,
            active_ids=picking.ids,
            active_model='stock.picking'
        ).create({})
        return_picking._onchange_picking_id()
        self.assertFalse(return_picking.return_reason_id)
        return_picking.return_reason_id = self.reason.id
        self.assertEqual(
            return_picking.return_reason_id.carrier_id, self.carrier_test_es)
        return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 2)
        picking_ret = self.sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(picking_ret.state, 'done')
        self.assertEqual(len(self.sale.order_line), 2)
        delivery_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_carrier)
        self.assertEqual(len(delivery_line), 1)
        self.assertTrue(delivery_line.is_delivery_return)
        product_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(product_line), 1)
        self.assertEqual(product_line.qty_delivered, 1)
        self.assertEqual(product_line.qty_invoiced, 0)
        self.assertEqual(product_line.qty_to_invoice, 1)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(delivery_line.qty_invoiced, 0)
        self.assertEqual(delivery_line.qty_to_invoice, 1)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(self.sale)
        invoice = self.sale.invoice_ids[0]
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(self.sale.invoice_ids), 1)
        self.assertEqual(self.sale.invoice_ids, invoice)
        self.assertEqual(invoice.move_type, 'out_invoice')
        invoice_line_product = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(invoice_line_product), 1)
        invoice_line_carrier = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_carrier)
        self.assertEqual(len(invoice_line_carrier), 1)
        self.assertEqual(invoice_line_product.quantity, 1)
        self.assertEqual(invoice_line_product.price_unit, 25)
        self.assertEqual(invoice_line_carrier.quantity, 1)
        self.assertEqual(invoice_line_carrier.price_unit, 3.99)
        self.assertEqual(round(invoice.amount_untaxed, 2), 28.99)
        self.assertEqual(product_line.qty_delivered, 1)
        self.assertEqual(product_line.qty_invoiced, 1)
        self.assertEqual(product_line.qty_to_invoice, 0)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(delivery_line.qty_invoiced, 1)
        self.assertEqual(delivery_line.qty_to_invoice, 0)

    def test_return_with_reason_with_carrier_domain_shipping_address(
            self):
        france_country = self.env.ref('base.fr')
        self.partner.country_id = france_country
        carrier_test_france = self.env['delivery.carrier'].create({
            'name': 'Carrier test send France',
            'delivery_type': 'fixed',
            'product_id': self.product_carrier.id,
            'fixed_price': 9.99,
            'country_ids': [(6, 0, france_country.ids)],
        })
        reason_carrier_fr = self.env['stock.picking.return.reason'].create({
            'name': 'Return reason test France',
            'carrier_id': carrier_test_france.id,
        })
        self.assertEqual(self.reason.pickings_count, 0)
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEqual(
            picking.partner_id.country_id, france_country)
        self.assertFalse(picking.return_reason_id)
        self.picking_transfer(picking, 2)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(self.sale.order_line.qty_to_invoice, 2)
        return_picking = self.env['stock.return.picking'].with_context(
            active_id=picking.id,
            active_ids=picking.ids,
            active_model='stock.picking'
        ).create({})
        return_picking._onchange_picking_id()
        self.assertFalse(return_picking.return_reason_id)
        domain_return_reason = return_picking._get_domain_return_reason_id()
        return_reason_ids = domain_return_reason[0][2]
        self.assertGreater(
            len(self.env['stock.picking.return.reason'].search([])),
            len(return_reason_ids))
        self.assertNotIn(self.reason_carrier_es.id, return_reason_ids)
        self.assertIn(reason_carrier_fr.id, return_reason_ids)
        return_picking.return_reason_id = reason_carrier_fr.id
        self.assertEqual(
            return_picking.return_reason_id.carrier_id, carrier_test_france)

    def test_return_with_reason_with_carrier_inv_policy_order_error(self):
        self.product.invoice_policy = 'order'
        self.reason.carrier_id = self.carrier_test_es.id
        self.assertEqual(self.reason.pickings_count, 0)
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.return_reason_id)
        self.picking_transfer(picking, 2)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(self.sale.order_line.qty_to_invoice, 2)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(self.sale)
        invoice = self.sale.invoice_ids[0]
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(self.sale.invoice_ids), 1)
        self.assertEqual(self.sale.invoice_ids, invoice)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(self.sale.order_line.qty_to_invoice, 0)
        self.assertEqual(len(self.sale.invoice_ids.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids.product_id, self.product)
        self.assertEqual(invoice.invoice_line_ids.quantity, 2)
        self.assertEqual(invoice.invoice_line_ids.price_unit, 25)
        self.assertEqual(invoice.amount_untaxed, 50)
        return_picking = self.env['stock.return.picking'].with_context(
            active_id=picking.id,
            active_ids=picking.ids,
            active_model='stock.picking'
        ).create({})
        return_picking._onchange_picking_id()
        self.assertFalse(return_picking.return_reason_id)
        return_picking.return_reason_id = self.reason.id
        self.assertEqual(
            return_picking.return_reason_id.carrier_id, self.carrier_test_es)
        return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 2)
        picking_ret = self.sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(picking_ret.state, 'done')
        self.assertEqual(len(self.sale.order_line), 2)
        delivery_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_carrier)
        self.assertEqual(len(delivery_line), 1)
        self.assertTrue(delivery_line.is_delivery_return)
        product_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(product_line), 1)
        self.assertEqual(product_line.qty_delivered, 1)
        self.assertEqual(product_line.qty_invoiced, 2)
        self.assertEqual(product_line.qty_to_invoice, 0)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(delivery_line.qty_invoiced, 0)
        self.assertEqual(delivery_line.qty_to_invoice, 1)

    def test_so_delivery_return_with_reason_with_carrier_inv_policy_delivery(
            self):
        self.reason.carrier_id = self.carrier_test_es.id
        self.assertEqual(self.reason.pickings_count, 0)
        self.assertEqual(self.sale.state, 'draft')
        self.assertEqual(len(self.sale.order_line), 1)
        other_product_carrier = self.env['product.product'].create({
            'name': 'Other carrier product',
            'type': 'service',
        })
        self.normal_delivery = self.env['delivery.carrier'].create({
            'name': 'Normal delivery test',
            'delivery_type': 'fixed',
            'product_id': other_product_carrier.id,
            'fixed_price': 3.75,
        })
        delivery_wizard = self.env['choose.delivery.carrier'].with_context({
            'default_order_id': self.sale.id,
            'default_carrier_id': self.normal_delivery.id,
        }).create({})
        delivery_wizard._onchange_carrier_id()
        self.assertEqual(delivery_wizard.display_price, 3.75)
        delivery_wizard.button_confirm()
        self.assertEqual(len(self.sale.order_line), 2)
        line_product = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(line_product), 1)
        self.assertEqual(line_product.price_unit, 25)
        line_delivery = self.sale.order_line.filtered(
            lambda ln: ln.product_id == other_product_carrier)
        self.assertEqual(len(line_delivery), 1)
        self.assertEqual(line_delivery.price_unit, 3.75)
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.return_reason_id)
        self.picking_transfer(picking, 2)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(line_product.qty_to_invoice, 2)
        self.assertEqual(line_delivery.qty_to_invoice, 1)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(self.sale)
        invoice = self.sale.invoice_ids[0]
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(self.sale.invoice_ids), 1)
        self.assertEqual(self.sale.invoice_ids, invoice)
        self.assertEqual(self.sale.amount_total, invoice.amount_total)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(line_product.qty_to_invoice, 0)
        self.assertEqual(line_delivery.qty_to_invoice, 0)
        self.assertEqual(len(self.sale.invoice_ids.invoice_line_ids), 2)
        invoice_line_product = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(invoice_line_product), 1)
        self.assertEqual(invoice_line_product.quantity, 2)
        self.assertEqual(invoice_line_product.price_unit, 25)
        invoice_line_delivery = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == other_product_carrier)
        self.assertEqual(len(invoice_line_delivery), 1)
        self.assertEqual(invoice_line_delivery.quantity, 1)
        self.assertEqual(invoice_line_delivery.price_unit, 3.75)
        self.assertEqual(invoice.amount_untaxed, 53.75)
        return_picking = self.env['stock.return.picking'].with_context(
            active_id=picking.id,
            active_ids=picking.ids,
            active_model='stock.picking'
        ).create({})
        return_picking._onchange_picking_id()
        self.assertFalse(return_picking.return_reason_id)
        return_picking.return_reason_id = self.reason.id
        self.assertEqual(
            return_picking.return_reason_id.carrier_id, self.carrier_test_es)
        return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 2)
        picking_ret = self.sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(picking_ret.state, 'done')
        self.assertEqual(len(self.sale.order_line), 3)
        delivery_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == other_product_carrier
            and ln.is_delivery_return is False)
        self.assertEqual(len(delivery_line), 1)
        self.assertFalse(delivery_line.is_delivery_return)
        delivery_line_return = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_carrier
            and ln.is_delivery_return is True)
        self.assertEqual(len(delivery_line_return), 1)
        self.assertTrue(delivery_line_return.is_delivery_return)
        product_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(product_line), 1)
        self.assertEqual(product_line.qty_delivered, 1)
        self.assertEqual(product_line.qty_invoiced, 2)
        self.assertEqual(product_line.qty_to_invoice, -1)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(delivery_line.qty_invoiced, 1)
        self.assertEqual(delivery_line.qty_to_invoice, 0)
        self.assertEqual(delivery_line_return.qty_delivered, 0)
        self.assertEqual(delivery_line_return.qty_invoiced, 0)
        self.assertEqual(delivery_line_return.qty_to_invoice, 1)
        invoice_ref = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(self.sale)
        self.assertEqual(len(self.sale.invoice_ids), 2)
        invoice_refund = self.sale.invoice_ids.filtered(
            lambda inv: inv.move_type == 'out_refund')
        self.assertEqual(len(invoice_refund), 1)
        self.assertEqual(invoice_refund, invoice_ref)
        self.assertEqual(len(invoice_refund.invoice_line_ids), 2)
        invoice_line_refund_product = invoice_refund.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(invoice_line_refund_product), 1)
        invoice_line_refund_carrier = invoice_refund.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_carrier)
        self.assertEqual(len(invoice_line_refund_carrier), 1)
        self.assertEqual(invoice_line_refund_product.quantity, 1)
        self.assertEqual(invoice_line_refund_product.price_unit, 25)
        self.assertEqual(invoice_line_refund_carrier.quantity, -1)
        self.assertEqual(invoice_line_refund_carrier.price_unit, 3.99)
        self.assertEqual(invoice_refund.amount_untaxed, 21.01)
        self.assertEqual(product_line.qty_delivered, 1)
        self.assertEqual(product_line.qty_invoiced, 1)
        self.assertEqual(product_line.qty_to_invoice, 0)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(delivery_line.qty_invoiced, 1)
        self.assertEqual(delivery_line.qty_to_invoice, 0)

    def test_so_delivery_return_with_reason_carrier_baseonrule_policy_delivery(
            self):
        carrier_base_on_rule = self.env['delivery.carrier'].create({
            'name': 'Carrier base on rule',
            'delivery_type': 'base_on_rule',
            'product_id': self.product_carrier.id,
            'price_rule_ids': [
                (0, 0, {
                    'variable': 'price',
                    'operator': '<=',
                    'max_value': 100,
                    'list_base_price': 10,
                    'variable_factor': 'price',
                }),
                (0, 0, {
                    'variable': 'price',
                    'operator': '<=',
                    'max_value': 99999999,
                    'list_base_price': 5,
                    'variable_factor': 'price',
                }),
            ],
        })
        self.reason.carrier_id = carrier_base_on_rule.id
        self.assertEqual(self.reason.pickings_count, 0)
        self.assertEqual(self.sale.state, 'draft')
        self.assertEqual(len(self.sale.order_line), 1)
        other_product_carrier = self.env['product.product'].create({
            'name': 'Other carrier product',
            'type': 'service',
        })
        normal_delivery_on_rule = self.env['delivery.carrier'].create({
            'name': 'Normal delivery base on rule test',
            'delivery_type': 'base_on_rule',
            'product_id': other_product_carrier.id,
            'price_rule_ids': [
                (0, 0, {
                    'variable': 'price',
                    'operator': '<=',
                    'max_value': 1,
                    'list_base_price': 1.75,
                    'variable_factor': 'price',
                }),
                (0, 0, {
                    'variable': 'price',
                    'operator': '<=',
                    'max_value': 99999999,
                    'list_base_price': 3.75,
                    'variable_factor': 'price',
                }),
            ],
        })
        delivery_wizard = self.env['choose.delivery.carrier'].with_context({
            'default_order_id': self.sale.id,
            'default_carrier_id': normal_delivery_on_rule.id,
        }).create({})
        delivery_wizard._onchange_carrier_id()
        self.assertEqual(delivery_wizard.display_price, 3.75)
        delivery_wizard.button_confirm()
        self.assertEqual(len(self.sale.order_line), 2)
        line_product = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(line_product), 1)
        self.assertEqual(line_product.price_unit, 25)
        line_delivery = self.sale.order_line.filtered(
            lambda ln: ln.product_id == other_product_carrier)
        self.assertEqual(len(line_delivery), 1)
        self.assertEqual(line_delivery.price_unit, 3.75)
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.return_reason_id)
        self.picking_transfer(picking, 2)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(line_product.qty_to_invoice, 2)
        self.assertEqual(line_delivery.qty_to_invoice, 1)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(self.sale)
        invoice = self.sale.invoice_ids[0]
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(self.sale.invoice_ids), 1)
        self.assertEqual(self.sale.invoice_ids, invoice)
        self.assertEqual(self.sale.amount_total, invoice.amount_total)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(line_product.qty_to_invoice, 0)
        self.assertEqual(line_delivery.qty_to_invoice, 0)
        self.assertEqual(len(self.sale.invoice_ids.invoice_line_ids), 2)
        invoice_line_product = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(invoice_line_product), 1)
        self.assertEqual(invoice_line_product.quantity, 2)
        self.assertEqual(invoice_line_product.price_unit, 25)
        invoice_line_delivery = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == other_product_carrier)
        self.assertEqual(len(invoice_line_delivery), 1)
        self.assertEqual(invoice_line_delivery.quantity, 1)
        self.assertEqual(invoice_line_delivery.price_unit, 3.75)
        self.assertEqual(invoice.amount_untaxed, 53.75)
        return_picking = self.env['stock.return.picking'].with_context(
            active_id=picking.id,
            active_ids=picking.ids,
            active_model='stock.picking'
        ).create({})
        return_picking._onchange_picking_id()
        self.assertFalse(return_picking.return_reason_id)
        return_picking.return_reason_id = self.reason.id
        self.assertEqual(
            return_picking.return_reason_id.carrier_id, carrier_base_on_rule)
        return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 2)
        picking_ret = self.sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(picking_ret.state, 'done')
        self.assertEqual(len(self.sale.order_line), 3)
        delivery_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == other_product_carrier
            and ln.is_delivery_return is False)
        self.assertEqual(len(delivery_line), 1)
        self.assertFalse(delivery_line.is_delivery_return)
        self.assertEqual(delivery_line.price_unit, 3.75)
        delivery_line_return = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_carrier
            and ln.is_delivery_return is True)
        self.assertEqual(len(delivery_line_return), 1)
        self.assertTrue(delivery_line_return.is_delivery_return)
        self.assertEqual(delivery_line_return.price_unit, 10)
        product_line = self.sale.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(product_line), 1)
        self.assertEqual(product_line.qty_delivered, 1)
        self.assertEqual(product_line.qty_invoiced, 2)
        self.assertEqual(product_line.qty_to_invoice, -1)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(delivery_line.qty_invoiced, 1)
        self.assertEqual(delivery_line.qty_to_invoice, 0)
        self.assertEqual(delivery_line_return.qty_delivered, 0)
        self.assertEqual(delivery_line_return.qty_invoiced, 0)
        self.assertEqual(delivery_line_return.qty_to_invoice, 1)
        invoice_ref = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(self.sale)
        self.assertEqual(len(self.sale.invoice_ids), 2)
        invoice_refund = self.sale.invoice_ids.filtered(
            lambda inv: inv.move_type == 'out_refund')
        self.assertEqual(len(invoice_refund), 1)
        self.assertEqual(invoice_refund, invoice_ref)
        self.assertEqual(len(invoice_refund.invoice_line_ids), 2)
        invoice_line_refund_product = invoice_refund.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(invoice_line_refund_product), 1)
        invoice_line_refund_carrier = invoice_refund.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_carrier)
        self.assertEqual(len(invoice_line_refund_carrier), 1)
        self.assertEqual(invoice_line_refund_product.quantity, 1)
        self.assertEqual(invoice_line_refund_product.price_unit, 25)
        self.assertEqual(invoice_line_refund_carrier.quantity, -1)
        self.assertEqual(invoice_line_refund_carrier.price_unit, 10)
        self.assertEqual(invoice_refund.amount_untaxed, 15)
        self.assertEqual(product_line.qty_delivered, 1)
        self.assertEqual(product_line.qty_invoiced, 1)
        self.assertEqual(product_line.qty_to_invoice, 0)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(delivery_line.qty_invoiced, 1)
        self.assertEqual(delivery_line.qty_to_invoice, 0)
