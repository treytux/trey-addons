###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestPurchaseOrderInvoice(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'supplier': True,
        })
        self.product1 = self.env['product.product'].create({
            'type': 'consu',
            'name': 'Test product1',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product2 = self.env['product.product'].create({
            'type': 'consu',
            'name': 'Test product2',
            'standard_price': 20,
            'list_price': 50,
        })

    def create_purchase(self):
        return self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })

    def create_purchase_line(self, purchase, product, qty):
        return self.env['purchase.order.line'].create({
            'order_id': purchase.id,
            'name': product.name,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'price_unit': 10,
            'product_qty': qty,
            'date_planned': fields.Date.today(),
        })

    def test_simple_line_and_backorder(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, self.product1, 100)
        purchase.button_confirm()
        self.assertEquals(purchase.invoice_status, 'no')
        self.assertEquals(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids
        picking.move_lines.write({'quantity_done': 60.0})
        backorder_wiz_id = picking.button_validate()['res_id']
        backorder_wiz = self.env['stock.backorder.confirmation'].browse(
            [backorder_wiz_id])
        backorder_wiz.process()
        backorder_picking = purchase.picking_ids[0]
        backorder_picking.action_confirm()
        backorder_picking.action_assign()
        for move in backorder_picking.move_lines:
            move.quantity_done = move.product_uom_qty
        backorder_picking.action_done()
        backorder_picking.date_done = datetime.now() + timedelta(days=31)
        self.assertEqual(picking.state, 'done')
        self.assertEquals(purchase.invoice_status, 'to invoice')
        wizard = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order'
        }).create({
            'method': 'divide',
        })
        wizard.action_invoice()
        self.assertEquals(purchase.invoice_count, 2)
        invoice1 = purchase.invoice_ids[0]
        invoice2 = purchase.invoice_ids[1]
        invoice_line_1 = invoice1.invoice_line_ids[0]
        invoice_line_2 = invoice2.invoice_line_ids[0]
        self.assertEquals(invoice_line_1.quantity, 40)
        self.assertEquals(invoice_line_2.quantity, 60)
        self.assertEquals(invoice1.amount_untaxed, 400)
        self.assertEquals(invoice1.amount_total, 460)
        self.assertEquals(invoice2.amount_untaxed, 600)
        self.assertEquals(invoice2.amount_total, 690)
        self.assertEquals(invoice1.type, 'in_invoice')
        self.assertEquals(invoice2.type, 'in_invoice')
        self.assertEquals(invoice_line_1.purchase_line_id.qty_invoiced, 100)
        self.assertEquals(purchase.invoice_status, 'invoiced')

    def test_diferent_lines_and_backorder(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, self.product1, 100)
        self.create_purchase_line(purchase, self.product2, 90)
        purchase.button_confirm()
        self.assertEquals(purchase.invoice_status, 'no')
        self.assertEquals(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids
        picking.move_lines[0].write({'quantity_done': 60.0})
        picking.move_lines[1].write({'quantity_done': 80.0})
        backorder_wiz_id = picking.button_validate()['res_id']
        backorder_wiz = self.env['stock.backorder.confirmation'].browse(
            [backorder_wiz_id])
        backorder_wiz.process()
        backorder_picking = purchase.picking_ids[0]
        backorder_picking.action_confirm()
        backorder_picking.action_assign()
        for move in backorder_picking.move_lines:
            move.quantity_done = move.product_uom_qty
        backorder_picking.action_done()
        backorder_picking.date_done = datetime.now() + timedelta(days=31)
        self.assertEqual(picking.state, 'done')
        self.assertEquals(purchase.invoice_status, 'to invoice')
        wizard = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order'
        }).create({
            'method': 'divide',
        })
        wizard.action_invoice()
        self.assertEquals(purchase.invoice_count, 2)
        invoice1 = purchase.invoice_ids[0]
        invoice2 = purchase.invoice_ids[1]
        self.assertEquals(invoice1.invoice_line_ids[0].quantity, 40)
        self.assertEquals(invoice1.invoice_line_ids[1].quantity, 10)
        self.assertEquals(invoice2.invoice_line_ids[0].quantity, 60)
        self.assertEquals(invoice2.invoice_line_ids[1].quantity, 80)
        self.assertEquals(invoice1.amount_untaxed, 500)
        self.assertEquals(invoice1.amount_total, 575)
        self.assertEquals(invoice2.amount_untaxed, 1400)
        self.assertEquals(invoice2.amount_total, 1610)
        self.assertEquals(
            invoice1.invoice_line_ids[0].purchase_line_id.qty_invoiced, 100)
        self.assertEquals(
            invoice1.invoice_line_ids[1].purchase_line_id.qty_invoiced, 90)
        self.assertEquals(purchase.invoice_status, 'invoiced')

    def test_cancelled_lines_and_backorder(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, self.product1, 100)
        self.create_purchase_line(purchase, self.product2, 90)
        purchase.button_confirm()
        self.assertEquals(purchase.invoice_status, 'no')
        self.assertEquals(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids
        picking.move_lines[0].write({'quantity_done': 60.0})
        picking.move_lines[1].write({'state': 'cancel'})
        backorder_wiz_id = picking.button_validate()['res_id']
        backorder_wiz = self.env['stock.backorder.confirmation'].browse(
            [backorder_wiz_id])
        backorder_wiz.process()
        backorder_picking = purchase.picking_ids[0]
        backorder_picking.action_confirm()
        backorder_picking.action_assign()
        for move in backorder_picking.move_lines:
            move.quantity_done = move.product_uom_qty
        backorder_picking.action_done()
        backorder_picking.date_done = datetime.now() + timedelta(days=31)
        self.assertEqual(picking.state, 'done')
        self.assertEquals(purchase.invoice_status, 'to invoice')
        wizard = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order'
        }).create({
            'method': 'divide',
        })
        wizard.action_invoice()
        self.assertEquals(purchase.invoice_count, 2)
        invoice1 = purchase.invoice_ids[0]
        invoice2 = purchase.invoice_ids[1]
        self.assertEquals(len(invoice1.invoice_line_ids), 1)
        self.assertEquals(invoice1.invoice_line_ids[0].quantity, 40)
        self.assertEquals(invoice2.invoice_line_ids[0].quantity, 60)
        self.assertEquals(invoice1.amount_untaxed, 400)
        self.assertEquals(invoice1.amount_total, 460)
        self.assertEquals(invoice2.amount_untaxed, 600)
        self.assertEquals(invoice2.amount_total, 690)
        self.assertEquals(
            invoice1.invoice_line_ids[0].purchase_line_id.qty_invoiced, 100)
        self.assertEquals(purchase.invoice_status, 'invoiced')

    def test_refund_invoice_purchase(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, self.product1, 100)
        purchase.button_confirm()
        self.assertEquals(purchase.invoice_status, 'no')
        self.assertEquals(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids
        picking.move_lines[0].write({'quantity_done': 100.0})
        picking.button_validate()
        self.assertEquals(purchase.invoice_status, 'to invoice')
        invoice_wizard = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order'
        }).create({
            'method': 'divide',
        })
        invoice_wizard.action_invoice()
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        invoice = purchase.invoice_ids[0]
        inv_line = invoice.invoice_line_ids[0]
        self.assertEquals(inv_line.quantity, 100)
        self.assertEquals(invoice.amount_total, 1150)
        self.assertEquals(invoice.type, 'in_invoice')
        self.assertEquals(inv_line.purchase_line_id.qty_invoiced, 100)
        invoice.action_invoice_open()
        return_wizard = self.env['stock.return.picking'].with_context({
            'active_id': purchase.picking_ids.id,
            'active_ids': purchase.picking_ids.ids,
            'active_model': 'stock.picking'
        }).create({})
        return_wizard.product_return_moves[0].write({
            'to_refund': True,
            'quantity': 22,
        })
        return_wizard.create_returns()
        self.assertEquals(len(purchase.picking_ids), 2)
        picking = purchase.picking_ids[0]
        picking.move_lines[0].write({'quantity_done': 22.0})
        picking.button_validate()
        self.assertEquals(
            purchase.picking_ids[0].picking_type_code, 'outgoing')
        self.assertEquals(
            purchase.picking_ids[1].picking_type_code, 'incoming')
        invoice_wizard2 = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order'
        }).create({
            'method': 'received',
        })
        invoice_wizard2.action_invoice()
        self.assertEquals(len(purchase.invoice_ids), 2)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        invoice_return = purchase.invoice_ids[0]
        invoice2 = purchase.invoice_ids[1]
        self.assertEquals(invoice_return.type, 'in_refund')
        self.assertEquals(invoice2.type, 'in_invoice')
        inv_line_return = invoice_return.invoice_line_ids[0]
        inv_line = invoice2.invoice_line_ids[0]
        self.assertEquals(inv_line_return.quantity, 22)
        self.assertEquals(inv_line.quantity, 100)
        self.assertEquals(invoice_return.amount_total, 220)
        self.assertEquals(invoice2.amount_total, 1150)
