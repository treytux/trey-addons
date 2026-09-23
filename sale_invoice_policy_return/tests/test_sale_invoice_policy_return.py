###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleInvoicePolicyReturn(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'company_id': False,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 20,
            'invoice_policy': 'delivery',
        })
        self.service = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test service',
            'standard_price': 1,
            'list_price': 2,
        })
        settings = self.env['res.config.settings'].create({})
        settings.execute()

    def picking_transfer(self, picking, qty):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = qty
        picking.button_validate()

    def test_sale_invoice_policy_order_picking_return_invoice(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'invoice_policy': 'order',
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': self.product.list_price,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(sale.order_line.qty_to_invoice, 1)
        self.assertEqual(sale.order_line.qty_invoiced, 0)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 1)
        self.assertEqual(len(invoice), 1)
        self.assertEqual(sale.invoice_ids, invoice)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(sale.amount_total, invoice.amount_total)
        self.assertEqual(sale.order_line.qty_to_invoice, 0)
        self.assertEqual(sale.order_line.qty_invoiced, 1)
        picking = sale.picking_ids[0]
        self.picking_transfer(picking, 1)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(sale.order_line.qty_to_invoice, 0)
        self.assertEqual(sale.order_line.qty_invoiced, 1)
        return_picking = self.env['stock.return.picking'].with_context(
            active_id=picking.id,
            active_ids=picking.ids,
            active_model='stock.picking',
        ).create({})
        return_picking._onchange_picking_id()
        return_picking.product_return_moves.write({
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 2)
        picking_ret = sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(picking_ret.state, 'done')
        self.assertEqual(sale.order_line.qty_to_invoice, -1)
        self.assertEqual(sale.order_line.qty_invoiced, 1)
        invoice_return = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 2)
        self.assertEqual(len(invoice_return), 1)
        self.assertIn(invoice_return, sale.invoice_ids)
        self.assertEqual(invoice_return.move_type, 'out_refund')
        self.assertEqual(sale.amount_total, invoice_return.amount_total)
        self.assertEqual(sale.order_line.qty_to_invoice, 0)
        self.assertEqual(sale.order_line.qty_invoiced, 0)

    def test_sale_with_service_and_product_sale_policy_order(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'invoice_policy': 'order',
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': self.product.list_price,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.service.id,
                    'price_unit': self.service.list_price,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        product_line = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(product_line), 1)
        service_line = sale.order_line.filtered(
            lambda ln: ln.product_id == self.service)
        self.assertEqual(len(service_line), 1)
        self.assertEqual(service_line.qty_to_invoice, 1)
        self.assertEqual(product_line.qty_to_invoice, 1)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 1)
        self.assertEqual(len(invoice), 1)
        self.assertEqual(sale.invoice_ids, invoice)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(sale.amount_total, invoice.amount_total)
        self.assertEqual(service_line.qty_invoiced, 1)
        self.assertEqual(product_line.qty_invoiced, 1)
        self.assertEqual(service_line.qty_to_invoice, 0)
        self.assertEqual(product_line.qty_to_invoice, 0)

    def test_sale_with_service_and_product_sale_policy_delivery(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'invoice_policy': 'delivery',
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': self.product.list_price,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.service.id,
                    'price_unit': self.service.list_price,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        product_line = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product)
        self.assertEqual(len(product_line), 1)
        service_line = sale.order_line.filtered(
            lambda ln: ln.product_id == self.service)
        self.assertEqual(len(service_line), 1)
        self.assertEqual(service_line.qty_to_invoice, 1)
        self.assertEqual(product_line.qty_to_invoice, 0)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 1)
        self.assertEqual(len(invoice), 1)
        self.assertEqual(sale.invoice_ids, invoice)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(service_line.qty_to_invoice, 0)
        self.assertEqual(service_line.qty_invoiced, 1)
        self.assertEqual(product_line.qty_to_invoice, 0)
        self.assertEqual(product_line.qty_invoiced, 0)
        picking = sale.picking_ids[0]
        self.picking_transfer(picking, 1)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(service_line.qty_to_invoice, 0)
        self.assertEqual(service_line.qty_invoiced, 1)
        self.assertEqual(product_line.qty_to_invoice, 1)
        self.assertEqual(product_line.qty_invoiced, 0)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 2)
        self.assertEqual(len(invoice), 1)
        self.assertEqual(service_line.qty_to_invoice, 0)
        self.assertEqual(service_line.qty_invoiced, 1)
        self.assertEqual(product_line.qty_to_invoice, 0)
        self.assertEqual(product_line.qty_invoiced, 1)

    def test_order_policy_non_delivered_product(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'invoice_policy': 'order',
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
            })],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(sale.order_line.qty_to_invoice, 5)
        sale.order_line._compute_qty_to_invoice()
        self.assertEqual(sale.order_line.qty_to_invoice, 5)
