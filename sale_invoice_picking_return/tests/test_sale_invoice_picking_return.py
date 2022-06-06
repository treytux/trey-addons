###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase


class TestSaleInvoicePickingReturn(TransactionCase):

    def setUp(self):
        super().setUp()
        type_revenue = self.env.ref('account.data_account_type_revenue')
        type_payable = self.env.ref('account.data_account_type_payable')
        account_customer = self.env['account.account'].create({
            'name': 'Customer',
            'code': 'XX_430',
            'user_type_id': type_payable.id,
            'reconcile': True,
        })
        account_supplier = self.env['account.account'].create({
            'name': 'Supplier',
            'code': 'XX_400',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': 'XX_700',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'property_account_receivable_id': account_customer.id,
            'property_account_payable_id': account_supplier.id,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': account_sale.id,
            'default_credit_account_id': account_sale.id,
        })
        tax_group_taxes = self.env.ref('account.tax_group_taxes')
        self.tax = self.env['account.tax'].create({
            'name': 'Tax for sale 10%',
            'type_tax_use': 'sale',
            'tax_group_id': tax_group_taxes.id,
            'amount_type': 'percent',
            'amount': 10.0,
        })
        self.product_delivery = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Physical product delivery',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'delivery',
        })
        self.product_order = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Physical product order',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'order',
        })

    def picking_transfer(self, picking, qty):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = qty
        picking.action_done()
        self.assertEquals(picking.state, 'done')

    def _create_invoice(self, sale, date=None):
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id,
        }
        payment_obj = self.env['sale.advance.payment.inv'].with_context(ctx)
        wizard = payment_obj.create({'advance_payment_method': 'all'})
        wizard.transfered_date = date and date or fields.Date.today()
        wizard.create_invoices()

    def test_invoice_sales_with_return_policy_delivery(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product_delivery.id,
                'name': self.product_delivery.name,
                'price_unit': 10.,
                'product_uom_qty': 10})],
        })
        sale.action_confirm()
        self.picking_transfer(sale.picking_ids[0], 10)
        self.assertEquals(sale.order_line.qty_delivered, 10)
        self._create_invoice(sale)
        self.assertEquals(len(sale.invoice_ids), 1)
        self.assertEquals(sale.order_line.qty_invoiced, 10)
        self.assertEquals(sale.order_line.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 1.0
        return_picking.product_return_moves.to_refund = True
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 1
        return_pick.move_lines.to_refund = 1
        return_pick.action_done()
        self.assertEquals(sale.order_line.qty_delivered, 9)
        self.assertEquals(sale.order_line.qty_invoiced, 10)
        self.assertEquals(sale.order_line.qty_to_invoice, -1)
        self._create_invoice(sale)
        self.assertEquals(sale.order_line.qty_delivered, 9)
        self.assertEquals(sale.order_line.qty_invoiced, 9)
        self.assertEquals(sale.order_line.qty_to_invoice, 0)
        self.assertEquals(len(sale.invoice_ids), 2)
        out_invoice = sale.invoice_ids.filtered(
            lambda i: i.type == 'out_invoice')
        self.assertEquals(len(out_invoice), 1)
        out_refund = sale.invoice_ids.filtered(
            lambda i: i.type == 'out_refund')
        self.assertEquals(len(out_refund), 1)
        self.assertEquals(len(out_refund.invoice_line_ids), 1)
        self.assertEquals(out_refund.invoice_line_ids[0].quantity, 1)

    def test_invoice_sales_with_return_policy_order(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product_order.id,
                'name': self.product_order.name,
                'price_unit': 10.,
                'product_uom_qty': 10})],
        })
        sale.action_confirm()
        self._create_invoice(sale)
        self.assertEquals(len(sale.invoice_ids), 1)
        self.assertEquals(sale.order_line.qty_invoiced, 10)
        self.assertEquals(sale.order_line.qty_to_invoice, 0)
        self.picking_transfer(sale.picking_ids[0], 10)
        self.assertEquals(sale.order_line.qty_delivered, 10)
        self.assertEquals(sale.order_line.qty_invoiced, 10)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 1.0
        return_picking.product_return_moves.to_refund = True
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 1
        return_pick.move_lines.to_refund = 1
        return_pick.action_done()
        self.assertEquals(sale.order_line.qty_delivered, 9)
        self.assertEquals(sale.order_line.qty_invoiced, 10)
        self.assertEquals(sale.order_line.qty_to_invoice, -1)
        self._create_invoice(sale)
        self.assertEquals(sale.order_line.qty_delivered, 9)
        self.assertEquals(sale.order_line.qty_invoiced, 9)
        self.assertEquals(sale.order_line.qty_to_invoice, 0)
        self.assertEquals(len(sale.invoice_ids), 2)
        out_invoice = sale.invoice_ids.filtered(
            lambda i: i.type == 'out_invoice')
        self.assertEquals(len(out_invoice), 1)
        out_refund = sale.invoice_ids.filtered(
            lambda i: i.type == 'out_refund')
        self.assertEquals(len(out_refund), 1)
        self.assertEquals(len(out_refund.invoice_line_ids), 1)
        self.assertEquals(out_refund.invoice_line_ids[0].quantity, 1)
