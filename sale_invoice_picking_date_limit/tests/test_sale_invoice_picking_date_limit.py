###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestSaleInvoiceAdvance(TransactionCase):

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
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Physical product',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'delivery',
        })
        location = self.env.ref('stock.stock_location_stock')
        inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': location.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.create({
            'inventory_id': inventory.id,
            'product_id': self.product.id,
            'product_qty': 100,
            'location_id': location.id,
        })
        inventory._action_done()

    def _confirm_picking(self, picking, quantity):
        picking.move_ids_without_package.quantity_done = quantity
        action = picking.button_validate()
        if not action:
            return
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()

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

    def test_invoice_sales(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': 10.,
                'product_uom_qty': 10})],
        })
        sale.action_confirm()
        self._confirm_picking(sale.picking_ids[0], 3)
        self.assertEquals(len(sale.picking_ids), 2)
        self._create_invoice(sale)
        self.assertEquals(len(sale.invoice_ids), 1)
        self.assertEquals(sale.invoice_ids.invoice_line_ids.quantity, 3)
        self.assertEquals(sale.order_line.qty_delivered, 3)
        self.assertEquals(sale.order_line.qty_invoiced, 3)
        self.assertEquals(sale.order_line.qty_to_invoice, 0)
        picking = sale.picking_ids.filtered(lambda p: p.state != 'done')
        self._confirm_picking(picking, 3)
        self.assertEquals(len(sale.picking_ids), 3)
        self._create_invoice(sale)
        self.assertEquals(len(sale.invoice_ids), 2)
        self.assertEquals(
            sum(sale.mapped('invoice_ids.invoice_line_ids.quantity')), 6)
        self.assertEquals(sale.order_line.qty_delivered, 6)
        self.assertEquals(sale.order_line.qty_invoiced, 6)
        self.assertEquals(sale.order_line.qty_to_invoice, 0)
        sale.invoice_ids.unlink()
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        done_pickings[0].date_done = (
            fields.Datetime.now() + timedelta(days=1))
        self._create_invoice(sale)
        self.assertEquals(len(sale.invoice_ids), 1)
        self.assertEquals(sale.invoice_ids.type, 'out_invoice')
        self.assertEquals(
            sum(sale.mapped('invoice_ids.invoice_line_ids.quantity')), 3)
        self.assertEquals(sale.order_line.qty_delivered, 6)
        self.assertEquals(sale.order_line.qty_invoiced, 3)
        self.assertEquals(sale.order_line.qty_to_invoice, 3)

    def test_invoice_sales_with_return(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': 10.,
                'product_uom_qty': 10})],
        })
        sale.action_confirm()
        self._confirm_picking(sale.picking_ids[0], 6)
        self._create_invoice(sale)
        self.assertEquals(sale.order_line.qty_delivered, 6)
        self.assertEquals(sale.order_line.qty_invoiced, 6)
        self.assertEquals(sale.order_line.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 1
        return_pick.move_lines.to_refund = 1
        return_pick.action_done()
        self.assertEquals(sale.order_line.qty_delivered, 5)
        self.assertEquals(sale.order_line.qty_invoiced, 6)
        self.assertEquals(sale.order_line.qty_to_invoice, -1)
        sale.invoice_ids.unlink()
        self.assertEquals(sale.order_line.qty_delivered, 5)
        self.assertEquals(sale.order_line.qty_invoiced, 0)
        self.assertEquals(sale.order_line.qty_to_invoice, 5)
        return_picking.date_done = (fields.Datetime.now() + timedelta(days=1))
        self._create_invoice(sale)
        self.assertEquals(sale.order_line.qty_delivered, 5)
        self.assertEquals(sale.order_line.qty_invoiced, 5)
        self.assertEquals(sale.order_line.qty_to_invoice, 0)
        self.assertEquals(len(sale.invoice_ids), 1)

    def test_invoice_sales_invoice_with_qty_lines_0(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': 10.,
                'product_uom_qty': 10})],
        })
        sale.action_confirm()
        self._confirm_picking(sale.picking_ids[0], 10)
        sale.picking_ids[0].date_done = (
            fields.Datetime.now() + timedelta(days=1))
        self._create_invoice(sale)
        self.assertEquals(sale.order_line.qty_delivered, 10)
        self.assertEquals(sale.order_line.qty_invoiced, 0)
        self.assertEquals(sale.order_line.qty_to_invoice, 10)
        self.assertEquals(len(sale.invoice_ids), 0)

    def test_invoice_sales_empty_invoice(self):
        other_product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Physical product Other',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'delivery',
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'price_unit': 10.,
                    'product_uom_qty': 10
                }),
                (0, 0, {
                    'product_id': other_product.id,
                    'name': other_product.name,
                    'price_unit': 10.,
                    'product_uom_qty': 10
                }),
            ],
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.move_ids_without_package[0].quantity_done = 10
        action = picking.button_validate()
        if action:
            wizard = self.env[action['res_model']].browse(action['res_id'])
            wizard.process()
        self.assertEquals(len(sale.picking_ids), 2)
        picking = sale.picking_ids[0]
        picking.move_ids_without_package[0].quantity_done = 10
        action = picking.button_validate()
        if action:
            wizard = self.env[action['res_model']].browse(action['res_id'])
            wizard.process()
        picking.date_done = fields.Datetime.now() + timedelta(days=10)
        self._create_invoice(sale)
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        self.assertEquals(invoice.invoice_line_ids[0].quantity, 10)
        self.assertEquals(len(invoice.picking_ids), 1)
        self.assertEquals(
            len(sale.order_line[0].move_ids.picking_id.invoice_ids), 1)
        self.assertEquals(sale.order_line[0].qty_delivered, 10)
        self.assertEquals(sale.order_line[0].qty_invoiced, 10)
        self.assertEquals(sale.order_line[0].qty_to_invoice, 0)
        self.assertEquals(
            len(sale.order_line[1].move_ids.picking_id.invoice_ids), 0)
        self.assertEquals(sale.order_line[1].qty_delivered, 10)
        self.assertEquals(sale.order_line[1].qty_invoiced, 0)
        self.assertEquals(sale.order_line[1].qty_to_invoice, 10)

    def test_invoice_sales_two_pickings(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'price_unit': 10.,
                    'product_uom_qty': 10
                }),
            ],
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.move_ids_without_package[0].quantity_done = 3
        action = picking.button_validate()
        if action:
            wizard = self.env[action['res_model']].browse(action['res_id'])
            wizard.process()
        self.assertEquals(len(sale.picking_ids), 2)
        picking = sale.picking_ids[0]
        picking.move_ids_without_package[0].quantity_done = 7
        picking.button_validate()
        picking.date_done = fields.Datetime.now() + timedelta(days=10)
        self._create_invoice(sale)
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        self.assertEquals(invoice.invoice_line_ids[0].quantity, 3)
        self.assertEquals(len(invoice.invoice_line_ids[0].move_line_ids), 1)
        self.assertEquals(len(invoice.picking_ids), 1)
