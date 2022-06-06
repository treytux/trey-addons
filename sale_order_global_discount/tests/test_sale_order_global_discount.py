###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderGlobalDiscount(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.discount_10 = self.env['res.partner.global_discount'].create({
            'name': 'Discount 10',
            'percent': 10,
        })
        self.discount_20 = self.env['res.partner.global_discount'].create({
            'name': 'Discount 20',
            'percent': 20,
        })
        self.discount_10_20 = self.env['res.partner.global_discount'].create({
            'name': 'Discount 10 + 20',
            'percent': '10+20',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
            'customer': True,
            'global_discount_ids': [
                (6, 0, [self.discount_10.id, self.discount_20.id])
            ],
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'name': 'One',
            'list_price': 10,
            'default_code': 'S1',
        })

    def test_multiple_discount(self):
        self.assertEquals(self.discount_10_20.total_percent, 28)

    def test_sale_order(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        sale.onchange_partner_id()
        self.assertEquals(len(sale.global_discount_ids), 2)
        sale.order_line = [
            (0, 0, {
                'product_id': self.product.id,
                'price_unit': 100,
                'product_uom_qty': 1,
            }),
        ]
        sale.order_line.product_id_change()
        sale.order_line.write({
            'price_unit': 100,
            'tax_id': [(6, 0, [])],
        })
        self.assertEquals(sale.order_line.price_unit, 100)
        self.assertEquals(sale.order_line.product_uom_qty, 1)
        self.assertEquals(sale.order_line.discount, 30)
        self.assertFalse(sale.order_line.tax_id)
        self.assertEquals(sale.amount_total, 70)
        self.assertEquals(sale.amount_untaxed_before_discount, 100)
        self.assertEquals(sale.amount_discount_untaxed, -30)
        sale.global_discount_ids = [(6, 0, self.discount_10_20.ids)]
        sale.order_line.unlink()
        sale.order_line = [
            (0, 0, {
                'product_id': self.product.id,
                'price_unit': 100,
                'product_uom_qty': 1,
            }),
        ]
        sale.order_line.product_id_change()
        sale.order_line.write({
            'price_unit': 100,
            'tax_id': [(6, 0, [])],
        })
        self.assertEquals(sale.order_line.price_unit, 100)
        self.assertEquals(sale.order_line.product_uom_qty, 1)
        self.assertEquals(sale.order_line.discount, 28)
        self.assertEquals(sale.amount_total, 72)
        self.assertEquals(sale.amount_untaxed_before_discount, 100)
        self.assertEquals(sale.amount_discount_untaxed, -28)
        sale.global_discount_ids = [
            (6, 0, self.discount_10_20.ids), (6, 0, self.discount_10.ids)]
        sale.order_line.unlink()
        sale.order_line = [
            (0, 0, {
                'product_id': self.product.id,
                'price_unit': 100,
                'product_uom_qty': 2,
            }),
        ]
        sale.order_line.product_id_change()
        sale.order_line.write({
            'price_unit': 75,
            'tax_id': [(6, 0, [])],
        })
        self.assertEquals(sale.amount_untaxed_before_discount, 150)
        self.assertEquals(sale.amount_discount_untaxed, -15)
        sale.order_line.unlink()
        sale.order_line = [
            (0, 0, {
                'product_id': self.product.id,
                'price_unit': 100,
                'product_uom_qty': 5,
            }),
        ]
        sale.order_line.product_id_change()
        sale.order_line.write({
            'price_unit': 500,
            'discount': 60,
            'tax_id': [(6, 0, [])],
        })
        self.assertEquals(sale.amount_untaxed_before_discount, 2500)
        self.assertEquals(sale.amount_discount_untaxed, -1500)

    def test_account_invoice(self):
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
        self.partner.property_account_receivable_id = account_customer.id
        self.partner.property_account_payable_id = account_supplier.id
        journal = self.env['account.journal'].create({
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
        self.product.taxes_id = [(6, 0, self.tax.ids)]
        journal = self.env['account.journal'].search([
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'sale')], limit=1)
        invoice = self.env['account.invoice'].create({
            'journal_id': journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'account_id': account_sale.id,
                    'price_unit': 100,
                    'quantity': 1,
                }),
            ],
        })
        invoice._onchange_partner_id()
        invoice.invoice_line_ids._onchange_product_id()
        invoice.invoice_line_ids.write({
            'price_unit': 100,
            'quantity': 1,
            'invoice_line_tax_ids': [(6, 0, [])],
        })
        self.assertEquals(invoice.invoice_line_ids.price_unit, 100)
        self.assertEquals(invoice.invoice_line_ids.quantity, 1)
        self.assertEquals(invoice.invoice_line_ids.discount, 30)
        self.assertFalse(invoice.invoice_line_ids.invoice_line_tax_ids)
        self.assertEquals(invoice.amount_total, 70)
        invoice.action_invoice_open()
