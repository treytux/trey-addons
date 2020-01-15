###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

# Important note! Install an account package


class TestSaleInvoiceAdvance(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env.ref(
            'product.expense_hotel_product_template').product_variant_id
        self.product.invoice_policy = 'order'

    def create_wizard(self, sales, method='advance'):
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sales.ids,
            'active_id': sales[0].id}
        payment_obj = self.env['sale.advance.payment.inv'].with_context(ctx)
        payment = payment_obj.create({
            'advance_payment_method': method})
        return payment.with_context(ctx)

    def test_invoice_advance_more_that_100(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 50.,
                'product_uom_qty': 2})]
        })
        self.assertEquals(sale.amount_total, 100.0)
        sale.action_confirm()
        wizard = self.create_wizard(sale)
        wizard.percents = '+50+50+50'
        with self.assertRaises(UserError):
            wizard.create_invoices()
        wizard.percents = '+50+50'
        with self.assertRaises(UserError):
            wizard.create_invoices()
        wizard.percents = '50+50'
        with self.assertRaises(UserError):
            wizard.create_invoices()
        wizard.percents = '99,2+0.8'
        with self.assertRaises(UserError):
            wizard.create_invoices()

    def test_invoice_advance(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 50.,
                'product_uom_qty': 2})]
        })
        self.assertEquals(sale.amount_total, 100.0)
        sale.action_confirm()
        wizard = self.create_wizard(sale)
        wizard.percents = '+50+25'
        self.assertEquals(wizard._get_percent_values(), [50, 25])
        wizard.create_invoices()
        self.assertEquals(len(sale.invoice_ids), 2)
        self.assertEquals(sum(sale.invoice_ids.mapped('amount_total')), 75)
        wizard = self.create_wizard(sale, method='all')
        wizard.create_invoices()
        self.assertEquals(len(sale.invoice_ids), 3)
        self.assertEquals(sum(sale.order_line.mapped('qty_to_invoice')), 0)

    def test_invoice_multi_advance_raise(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 50.,
                'product_uom_qty': 2})]
        })
        sale.action_confirm()
        wizard = self.create_wizard(sale)
        wizard.percents = '50'
        wizard.create_invoices()
        self.assertEquals(sale.amount_advanced, 50)
        self.assertEquals(sale.percent_advanced, 50)
        wizard = self.create_wizard(sale)
        wizard.percents = '50'
        with self.assertRaises(UserError):
            wizard.create_invoices()

    def test_invoice_multi_advance(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 50.,
                'product_uom_qty': 2})]
        })
        self.assertEquals(sale.amount_total, 100.0)
        sale.action_confirm()
        self.assertEquals(sale.amount_advanced, 0)
        self.assertEquals(sale.percent_advanced, 0)
        wizard = self.create_wizard(sale)
        wizard.percents = '50'
        wizard.create_invoices()
        self.assertEquals(len(sale.invoice_ids), 1)
        self.assertEquals(sum(sale.invoice_ids.mapped('amount_total')), 50)
        self.assertEquals(sale.amount_advanced, 50)
        self.assertEquals(sale.percent_advanced, 50)
        down_lines = sale.order_line.filtered(lambda l: l.is_downpayment)
        self.assertEquals(len(down_lines), 1)
        self.assertEquals(down_lines.qty_invoiced, 1)
        wizard = self.create_wizard(sale)
        wizard.percents = '25'
        wizard.create_invoices()
        self.assertEquals(len(sale.invoice_ids), 2)
        self.assertEquals(sum(sale.invoice_ids.mapped('amount_total')), 75)
        wizard = self.create_wizard(sale, method='all')
        wizard.create_invoices()
        self.assertEquals(len(sale.invoice_ids), 3)
        self.assertEquals(sum(sale.order_line.mapped('qty_to_invoice')), 0)
        self.assertEquals(sale.amount_advanced, 75)
        self.assertEquals(sale.percent_advanced, 75)
        sale_lines = sale.order_line.filtered(lambda l: not l.is_downpayment)
        self.assertEquals(len(sale_lines), 1)
        self.assertEquals(
            len(sale_lines.invoice_lines.invoice_id.invoice_line_ids), 3)

    def test_invoice_with_taxes(self):
        tax = self.env['account.tax'].create({
            'name': 'Tax Test 10%',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 10,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'tax_id': [(6, 0, tax.ids)],
                'price_unit': 50.,
                'product_uom_qty': 2})]
        })
        self.assertEquals(sale.amount_untaxed, 100)
        self.assertEquals(sale.amount_tax, 10)
        self.assertEquals(sale.amount_total, 110)
        sale.action_confirm()
        self.assertEquals(sale.amount_advanced, 0)
        self.assertEquals(sale.percent_advanced, 0)
        wizard = self.create_wizard(sale)
        wizard.write({
            'deposit_taxes_id': [(6, 0, tax.ids)],
            'percents': 50,
        })
        wizard.create_invoices()
        self.assertEquals(len(sale.invoice_ids), 1)
        self.assertEquals(sum(sale.invoice_ids.mapped('amount_untaxed')), 50)
        self.assertEquals(sum(sale.invoice_ids.mapped('amount_tax')), 5)
        self.assertEquals(sum(sale.invoice_ids.mapped('amount_total')), 55)
