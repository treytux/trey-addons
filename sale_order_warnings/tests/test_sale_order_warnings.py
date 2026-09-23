###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleOrderWarnings(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })
        self.tax_exempt = self.env['account.tax'].create({
            'name': 'Exempt 0%',
            'amount': 0.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': self.env.company.id,
        })

    def create_sale(self, taxes=None):
        taxes = taxes if taxes is not None else []
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10,
                'tax_id': [(6, 0, taxes)],
            })],
        })
        return sale

    def test_company_not_checked(self):
        self.company.show_missing_taxes_in_so = False
        sale_order = self.create_sale()
        self.assertEqual(sale_order.missing_taxes, False)

    def test_company_checked_without_taxes(self):
        self.company.show_missing_taxes_in_so = True
        sale_order = self.create_sale()
        self.assertEqual(sale_order.missing_taxes, True)

    def test_company_checked_with_zero_percent_tax(self):
        self.company.show_missing_taxes_in_so = True
        sale_order = self.create_sale(taxes=[self.tax_exempt.id])
        self.assertEqual(sale_order.missing_taxes, False)
