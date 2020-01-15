###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import logging
_log = logging.getLogger(__name__)

# Important note! Install an account package


class TestSaleReturn(TransactionCase):

    def setUp(self):
        super().setUp()
        domain = [('company_id', '=', self.env.ref('base.main_company').id)]
        if not self.env['account.account'].search_count(domain):
            _log.warn(
                'Test skipped because there is no chart of account defined')
            self.skipTest('No Chart of account found')
            return
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 50,
            'list_price': 50,
        })

    def test_sale_invoice(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': 50.,
                'product_uom_qty': 2})],
        })
        with self.assertRaises(ValidationError):
            sale.advance_formula = 'one+1'
        with self.assertRaises(ValidationError):
            sale.advance_formula = '100+1'
        with self.assertRaises(ValidationError):
            sale.advance_formula = '51+51'
        with self.assertRaises(ValidationError):
            sale.advance_formula = '20+30+51'
        sale.advance_formula = '50+30+20'
        sale.action_confirm()
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id}
        payment_obj = self.env['sale.advance.payment.inv'].with_context(ctx)
        wizard = payment_obj.create({'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEquals(len(sale.invoice_ids), 3)
        for invoice in sale.invoice_ids:
            self.assertIn(invoice.amount_untaxed, [50, 30, 20])
            self.assertIn(invoice.percent_advanced, [80, 0])

    def test_invoice_3_sales_only_one_with_formula(self):
        sales = self.env['sale.order']
        for i in range(3):
            sales |= sales.create({
                'partner_id': self.partner.id,
                'order_line': [(0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'price_unit': 50.,
                    'product_uom_qty': 2})],
            })
        sales[0].advance_formula = '50+30+20'
        sales.action_confirm()
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sales.ids,
            'active_id': sales[0].id}
        payment_obj = self.env['sale.advance.payment.inv'].with_context(ctx)
        wizard = payment_obj.create({'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEquals(len(sales[0].invoice_ids), 1)
        self.assertEquals(len(sales[1].invoice_ids), 1)
        self.assertEquals(len(sales[2].invoice_ids), 1)
        self.assertEquals(sales[0].invoice_ids, sales[1].invoice_ids)
        self.assertEquals(sales[1].invoice_ids, sales[2].invoice_ids)

    def test_invoice_3_sales_same_formula(self):
        sales = self.env['sale.order']
        for i in range(3):
            sales |= sales.create({
                'partner_id': self.partner.id,
                'advance_formula': '50+30+20',
                'order_line': [(0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'price_unit': 50.,
                    'product_uom_qty': 2})],
            })
        self.assertEquals(sales[0].advance_formula, '50+30+20')
        sales.action_confirm()
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sales.ids,
            'active_id': sales[0].id}
        payment_obj = self.env['sale.advance.payment.inv'].with_context(ctx)
        wizard = payment_obj.create({'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEquals(len(sales[0].invoice_ids), 3)
        self.assertEquals(len(sales[1].invoice_ids), 3)
        self.assertEquals(len(sales[2].invoice_ids), 3)
        for invoice in sales[0].invoice_ids:
            self.assertIn(invoice.percent_advanced, [80, 0])

    def test_invoice_with_taxes(self):
        tax = self.env['account.tax'].create({
            'name': 'Tax Test 10%',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 10,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'advance_formula': '50',
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
        product = self.env.ref('account_invoice_advance.advance_product')
        product.taxes_id = [(6, 0, tax.ids)]
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id}
        payment_obj = self.env['sale.advance.payment.inv'].with_context(ctx)
        wizard = payment_obj.create({'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEquals(len(sale.invoice_ids), 2)
        original_invoice = sale.invoice_ids.filtered(
            lambda i: i.advance_invoice_ids)
        self.assertEquals(
            original_invoice.invoice_line_ids[1].invoice_line_tax_ids.name,
            tax.name)
        self.assertEquals(original_invoice.amount_advanced, 50)
        self.assertEquals(original_invoice.percent_advanced, 50)
        self.assertEquals(original_invoice.amount_untaxed, 50)
        self.assertEquals(original_invoice.amount_tax, 5)
        invoice = sale.invoice_ids.filtered(lambda i: i.advance_invoice_id)
        self.assertEquals(invoice.amount_untaxed, 50)
        self.assertEquals(invoice.amount_tax, 5)
        self.assertEquals(invoice.amount_total, 55)

    def test_invoice_with_lines(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 50.,
                'product_uom_qty': 2})],
            'advance_line_ids': [
                (0, 0, {
                    'name': 'First',
                    'percent': 10,
                    'date': fields.Date.today() + relativedelta(months=0),
                }),
                (0, 0, {
                    'name': 'Second',
                    'percent': 20,
                    'date': fields.Date.today() + relativedelta(months=1),
                }),
                (0, 0, {
                    'name': 'Third',
                    'percent': 30,
                    'date': fields.Date.today() + relativedelta(months=2),
                }),
            ]
        })
        formula = '+'.join([str(v) for v in sale.get_advance_percents() if v])
        self.assertEquals(formula, '10.0+20.0+30.0')
        self.assertEquals(sale.amount_untaxed, 100)
        sale.action_confirm()
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id}
        payment_obj = self.env['sale.advance.payment.inv'].with_context(ctx)
        wizard = payment_obj.create({'advance_payment_method': 'all'})
        wizard.create_invoices()
        self.assertEquals(len(sale.invoice_ids), 4)
        inv_final = sale.invoice_ids.filtered(lambda i: i.advance_invoice_ids)
        self.assertFalse(inv_final.date_invoice, False)
        inv_advance = sale.invoice_ids.filtered(lambda i: i.advance_invoice_id)
        self.assertEquals(len(inv_advance), 3)
        self.assertTrue(inv_advance[0].date_invoice)
        self.assertTrue(inv_advance[1].date_invoice)
        self.assertTrue(inv_advance[2].date_invoice)
        names = inv_advance.mapped('invoice_line_ids.name')
        self.assertEquals(len(names), 3)
        self.assertTrue([n for n in names if 'First' in n])
        self.assertTrue([n for n in names if 'Second' in n])
        self.assertTrue([n for n in names if 'Third' in n])
