###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrderInvoiceDay(TransactionCase):

    def setUp(self):
        super().setUp()
        self.invoice_day_a = self.env['res.partner.invoice_day'].create({
            'name': 'INV-DAY-A',
        })
        self.product_a = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product a',
            'default_code': 'TESTPR_A',
            'standard_price': 10,
            'list_price': 30,
        })
        self.partner_a = self.env['res.partner'].create({
            'name': 'Test partner A',
            'is_company': True,
            'sale_invoice_day_id': self.invoice_day_a.id,
        })
        self.partner_b = self.env['res.partner'].create({
            'name': 'Test partner B',
            'is_company': True,
        })

    def test_module_loads(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'sale_order_invoice_day'),
        ])
        self.assertEqual(module.state, 'installed')

    def test_sale_with_invoice_day(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 1,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale._onchange_partner_id_invoice_day()
        sale.action_confirm()
        self.assertEqual(
            sale.invoice_day_id, self.partner_a.sale_invoice_day_id)

    def test_sale_without_invoice_day(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner_b.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 1,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale._onchange_partner_id_invoice_day()
        sale.action_confirm()
        self.assertFalse(sale.invoice_day_id)
        self.assertFalse(self.partner_b.sale_invoice_day_id)

    def test_invoicing_day_single_day(self):
        invoice_day = self.env['res.partner.invoice_day'].create({
            'name': 'DIA 25',
            'days': '25',
        })
        self.assertFalse(invoice_day._is_invoicing_day(date(2026, 9, 25)))
        self.assertTrue(invoice_day._is_invoicing_day(date(2026, 9, 26)))
        self.assertFalse(invoice_day._is_invoicing_day(date(2026, 9, 27)))

    def test_invoicing_day_multiple_days(self):
        invoice_day = self.env['res.partner.invoice_day'].create({
            'name': 'DIAS 10 Y 25',
            'days': '10, 25',
        })
        self.assertTrue(invoice_day._is_invoicing_day(date(2026, 9, 11)))
        self.assertTrue(invoice_day._is_invoicing_day(date(2026, 9, 26)))
        self.assertFalse(invoice_day._is_invoicing_day(date(2026, 9, 12)))

    def test_invoicing_day_end_of_month(self):
        invoice_day = self.env['res.partner.invoice_day'].create({
            'name': 'FINAL DE MES',
            'days': '31',
        })
        self.assertTrue(invoice_day._is_invoicing_day(date(2026, 3, 1)))
        self.assertFalse(invoice_day._is_invoicing_day(date(2026, 2, 28)))
        self.assertTrue(invoice_day._is_invoicing_day(date(2026, 5, 1)))
        self.assertTrue(invoice_day._is_invoicing_day(date(2026, 8, 1)))

    def test_invoicing_day_combined_with_end_of_month(self):
        invoice_day = self.env['res.partner.invoice_day'].create({
            'name': 'DIAS 15 Y FINAL DE MES',
            'days': '15,31',
        })
        self.assertTrue(invoice_day._is_invoicing_day(date(2026, 9, 16)))
        self.assertTrue(invoice_day._is_invoicing_day(date(2026, 10, 1)))
        self.assertFalse(invoice_day._is_invoicing_day(date(2026, 9, 17)))

    def test_invoicing_day_invalid_value(self):
        invoice_day = self.env['res.partner.invoice_day'].create({
            'name': 'INVALID',
        })
        with self.assertRaises(ValidationError):
            invoice_day.write({'days': '15,abc'})
        with self.assertRaises(ValidationError):
            invoice_day.write({'days': '32'})
