###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase


class TestPurchaseOrderInvoice(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'supplier': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })

    def create_purchase(self):
        return self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })

    def create_purchase_line(self, purchase, qty):
        return self.env['purchase.order.line'].create({
            'order_id': purchase.id,
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'price_unit': 10,
            'product_qty': qty,
            'date_planned': fields.Date.today(),
        })

    def picking_transfer(self, picking, qty):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = qty
        picking.action_done()

    def test_invoice_purchase_received(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, 100)
        purchase.button_confirm()
        self.assertEquals(purchase.invoice_status, 'no')
        self.assertEquals(len(purchase.picking_ids), 1)
        self.picking_transfer(purchase.picking_ids[0], 40)
        self.assertEquals(purchase.invoice_status, 'to invoice')
        wizard = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order'
        }).create({
            'method': 'received',
        })
        wizard.action_invoice()
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        invoice = purchase.invoice_ids[0]
        inv_line = invoice.invoice_line_ids[0]
        self.assertEquals(inv_line.quantity, 40)
        self.assertEquals(invoice.amount_total, 400)
        self.assertEquals(invoice.type, 'in_invoice')
        self.assertEquals(inv_line.purchase_line_id.qty_invoiced, 40)

    def test_invoice_purchase_all(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, 100)
        purchase.button_confirm()
        self.assertEquals(purchase.invoice_status, 'no')
        self.assertEquals(len(purchase.picking_ids), 1)
        self.picking_transfer(purchase.picking_ids[0], 40)
        self.assertEquals(purchase.invoice_status, 'to invoice')
        wizard = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order'
        }).create({
            'method': 'all',
        })
        wizard.action_invoice()
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        invoice = purchase.invoice_ids[0]
        inv_line = invoice.invoice_line_ids[0]
        self.assertEquals(inv_line.quantity, inv_line.purchase_line_id.product_qty)
        self.assertEquals(invoice.amount_total, purchase.amount_total)
        self.assertEquals(invoice.type, 'in_invoice')
        self.assertEquals(inv_line.purchase_line_id.qty_invoiced, 100)

    def test_invoice_purchase_all_not_invoiced(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, 100)
        purchase.button_confirm()
        self.assertEquals(purchase.invoice_status, 'no')
        self.assertEquals(len(purchase.picking_ids), 1)
        self.picking_transfer(purchase.picking_ids[0], 40)
        self.assertEquals(purchase.invoice_status, 'to invoice')
        wizard = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order'
        }).create({
            'method': 'all-not-invoiced',
        })
        wizard.action_invoice()
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        invoice = purchase.invoice_ids[0]
        inv_line = invoice.invoice_line_ids[0]
        self.assertEquals(inv_line.quantity, 100)
        self.assertEquals(invoice.amount_total, purchase.amount_total)
        self.assertEquals(invoice.type, 'in_invoice')
        self.assertEquals(inv_line.purchase_line_id.qty_invoiced, 100)

    def test_invoice_purchase_mixed(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, 100)
        purchase.button_confirm()
        self.assertEquals(purchase.invoice_status, 'no')
        self.assertEquals(len(purchase.picking_ids), 1)
        self.picking_transfer(purchase.picking_ids[0], 40)
        self.assertEquals(purchase.invoice_status, 'to invoice')
        wizard = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order'
        }).create({
            'method': 'received',
        })
        wizard.action_invoice()
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        invoice = purchase.invoice_ids[0]
        inv_line = invoice.invoice_line_ids[0]
        self.assertEquals(inv_line.quantity, 40)
        self.assertEquals(invoice.amount_total, 400)
        self.assertEquals(invoice.type, 'in_invoice')
        self.assertEquals(inv_line.purchase_line_id.qty_invoiced, 40)
        wizard = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order'
        }).create({
            'method': 'all-not-invoiced',
        })
        wizard.action_invoice()
        self.assertEquals(len(purchase.invoice_ids), 2)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        invoice1 = purchase.invoice_ids[0]
        invoice2 = purchase.invoice_ids[1]
        inv_line1 = invoice1.invoice_line_ids[0]
        inv_line2 = invoice2.invoice_line_ids[0]
        self.assertEquals(inv_line1.quantity, 60)
        self.assertEquals(inv_line2.quantity, 40)
        self.assertEquals(invoice1.amount_total, 600)
        self.assertEquals(invoice2.amount_total, 400)
        self.assertEquals(invoice1.type, 'in_invoice')
        self.assertEquals(inv_line1.purchase_line_id.qty_invoiced, 100)

    def test_refund_invoice_purchase(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, 100)
        purchase.button_confirm()
        self.assertEquals(purchase.invoice_status, 'no')
        self.assertEquals(len(purchase.picking_ids), 1)
        self.picking_transfer(purchase.picking_ids[0], 100)
        self.assertEquals(purchase.invoice_status, 'to invoice')
        invoice_wizard = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': purchase.ids,
            'active_model': 'purchase.order'
        }).create({
            'method': 'received',
        })
        invoice_wizard.action_invoice()
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        invoice = purchase.invoice_ids[0]
        inv_line = invoice.invoice_line_ids[0]
        self.assertEquals(inv_line.quantity, 100)
        self.assertEquals(invoice.amount_total, purchase.amount_total)
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
        self.picking_transfer(purchase.picking_ids[0], 22)
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
        self.assertEquals(invoice2.amount_total, 1000)

    def test_invoice_multiple(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, 100)
        purchase.button_confirm()
        purchase2 = self.create_purchase()
        self.create_purchase_line(purchase2, 200)
        purchase2.button_confirm()
        wizard = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': [purchase.id, purchase2.id],
            'active_model': 'purchase.order'
        }).create({
            'method': 'all',
        })
        wizard.action_invoice()
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(
            purchase.invoice_ids.origin,
            ','.join([purchase.name, purchase2.name]))
        self.assertEquals(len(purchase.invoice_ids), 1)
        invoice = purchase.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 2)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        self.assertEquals(purchase2.invoice_status, 'invoiced')
        invoice = purchase.invoice_ids[0]
        inv_line = invoice.invoice_line_ids[0]
        self.assertEquals(
            inv_line.quantity, inv_line.purchase_line_id.product_qty)
        self.assertEquals(
            invoice.amount_total,
            purchase.amount_total + purchase2.amount_total)
        self.assertEquals(invoice.type, 'in_invoice')
        self.assertEquals(inv_line.purchase_line_id.qty_invoiced, 100)
        invoice = purchase2.invoice_ids[0]
        inv_line = invoice.invoice_line_ids[0]
        self.assertEquals(inv_line.quantity, inv_line.purchase_line_id.product_qty)
        self.assertEquals(invoice.type, 'in_invoice')

    def test_invoice_multiple_not_join(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, 100)
        purchase.button_confirm()
        purchase2 = self.create_purchase()
        self.create_purchase_line(purchase2, 200)
        purchase2.button_confirm()
        wizard = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': [purchase.id, purchase2.id],
            'active_model': 'purchase.order',
        }).create({
            'method': 'all',
            'join_purchases': False,
        })
        wizard.action_invoice()
        self.assertNotEqual(purchase.invoice_ids, purchase2.invoice_ids)

    def test_invoice_multiple_different_partners(self):
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, 100)
        purchase.button_confirm()
        purchase2 = self.create_purchase()
        other_partner = self.env['res.partner'].create({
            'name': 'Other partner test',
            'supplier': True,
        })
        purchase2.partner_id = other_partner.id
        self.create_purchase_line(purchase2, 200)
        purchase2.button_confirm()
        wizard = self.env['purchase.order.invoice'].with_context({
            'active_id': purchase.id,
            'active_ids': [purchase.id, purchase2.id],
            'active_model': 'purchase.order',
        }).create({
            'method': 'all',
        })
        invoices = self.env['account.invoice'].search(
            [('type', '=', 'in_invoice')])
        wizard.action_invoice()
        new_invoices = self.env['account.invoice'].search(
            [('type', '=', 'in_invoice')])
        self.assertEquals(len(new_invoices) - len(invoices), 2)
        self.assertNotEqual(purchase.partner_id, purchase2.partner_id)
        self.assertNotEqual(purchase.invoice_ids, purchase2.invoice_ids)
