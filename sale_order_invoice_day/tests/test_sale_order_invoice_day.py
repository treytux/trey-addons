###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleOrderInvoiceProductCategory(TransactionCase):
    def setUp(self):
        super().setUp()
        invoice_day_a = self.env['res.partner.invoice_day'].create({
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
            'customer': True,
            'is_company': True,
            'sale_invoice_day_id': invoice_day_a.id,
        })
        self.partner_b = self.env['res.partner'].create({
            'name': 'Test partner B',
            'customer': True,
            'is_company': True,
        })

    def test_sale_with_invoice_day(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 1,
                    'product_uom_qty': 1}),
            ]
        })
        sale.onchange_partner_id()
        sale.action_confirm()
        self.assertEquals(
            sale.invoice_day_id, self.partner_a.sale_invoice_day_id)

    def test_sale_without_invoice_day(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner_b.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 1,
                    'product_uom_qty': 1}),
            ]
        })
        sale.onchange_partner_id()
        sale.action_confirm()
        self.assertEquals(
            sale.invoice_day_id, self.partner_b.sale_invoice_day_id)
        self.assertFalse(sale.invoice_day_id)
        self.assertFalse(self.partner_b.sale_invoice_day_id)
