###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestProductExtraTaxFees(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.account_70 = self.env['account.account'].create({
            'code': '70000',
            'name': '70000',
            'user_type_id': self.ref('account.data_account_type_revenue'),
        })
        self.product_tmpl_a = self.env['product.template'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Service product a',
            'standard_price': 10,
            'list_price': 100,
            'property_account_income_id': self.account_70.id,
        })
        self.product_tmpl_b = self.env['product.template'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Service product b',
            'standard_price': 10,
            'list_price': 100,
            'property_account_income_id': self.account_70.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'country_id': self.env.ref('base.es').id,
        })
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
        self.account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': 'XX_700',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.partner.property_account_receivable_id = account_customer.id
        self.partner.property_account_payable_id = account_supplier.id
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': self.account_sale.id,
            'default_credit_account_id': self.account_sale.id,
        })
        tax_group_taxes = self.env.ref('account.tax_group_taxes')
        self.tax = self.env['account.tax'].create({
            'name': 'Tax for sale 10%',
            'type_tax_use': 'sale',
            'tax_group_id': tax_group_taxes.id,
            'amount_type': 'percent',
            'amount': 10.0,
        })
        self.product_tmpl_a.taxes_id = [(6, 0, self.tax.ids)]

    def test_product_extra_fees_fixed_selected_products(self):
        self.assertFalse(self.product_tmpl_a.tax_fee_ids)
        tax_fee = self.env['account.tax.fee'].create({
            'name': 'Ecotax A',
            'apply_on': 'selected_products',
            'product_tmpl_ids': [(4, self.product_tmpl_a.id)],
            'country_id': self.env.ref('base.es').id,
            'amount': 12.45,
            'compute_method': 'fixed',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_tmpl_a.product_variant_ids.id,
                'name': self.product_tmpl_a.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice.action_invoice_open()
        invoice_line = invoice.invoice_line_ids[0]
        self.assertEquals(len(invoice_line.tax_fee_ids), 1)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_amount, 12.45)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_id.id, tax_fee.id)
        self.assertEquals(invoice_line.tax_fee_amount, 12.45)

    def test_product_extra_fees_fixed_all_products(self):
        self.assertFalse(self.product_tmpl_a.tax_fee_ids)
        tax_fee = self.env['account.tax.fee'].create({
            'name': 'Ecotax A',
            'apply_on': 'all',
            'country_id': self.env.ref('base.es').id,
            'amount': 12.45,
            'compute_method': 'fixed',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_tmpl_a.product_variant_ids.id,
                'name': self.product_tmpl_a.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice.action_invoice_open()
        invoice_line = invoice.invoice_line_ids[0]
        self.assertEquals(len(invoice_line.tax_fee_ids), 1)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_amount, 12.45)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_id.id, tax_fee.id)
        self.assertEquals(invoice_line.tax_fee_amount, 12.45)

    def test_product_extra_fees_formula_selected_products(self):
        self.assertFalse(self.product_tmpl_a.tax_fee_ids)
        tax_fee = self.env['account.tax.fee'].create({
            'name': 'Ecotax formula',
            'apply_on': 'selected_products',
            'product_tmpl_ids': [(4, self.product_tmpl_a.id)],
            'country_id': self.env.ref('base.es').id,
            'amount': 22.5,
            'formula': 'result=tax_fee.amount+5',
            'compute_method': 'formula',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_tmpl_a.product_variant_ids.id,
                'name': self.product_tmpl_a.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice.action_invoice_open()
        invoice_line = invoice.invoice_line_ids[0]
        self.assertEquals(len(invoice_line.tax_fee_ids), 1)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_amount, 27.5)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_id.id, tax_fee.id)
        self.assertEquals(invoice_line.tax_fee_amount, 27.5)

    def test_product_extra_fees_formula_all_products(self):
        self.assertFalse(self.product_tmpl_a.tax_fee_ids)
        tax_fee = self.env['account.tax.fee'].create({
            'name': 'Ecotax formula',
            'apply_on': 'all',
            'country_id': self.env.ref('base.es').id,
            'amount': 22.5,
            'formula': 'result=tax_fee.amount+5',
            'compute_method': 'formula',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_tmpl_a.product_variant_ids.id,
                'name': self.product_tmpl_a.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice.action_invoice_open()
        invoice_line = invoice.invoice_line_ids[0]
        self.assertEquals(len(invoice_line.tax_fee_ids), 1)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_amount, 27.5)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_id.id, tax_fee.id)
        self.assertEquals(invoice_line.tax_fee_amount, 27.5)

    def test_product_extra_fees_no_country(self):
        self.assertFalse(self.product_tmpl_a.tax_fee_ids)
        self.env['account.tax.fee'].create({
            'name': 'Ecotax A',
            'apply_on': 'selected_products',
            'product_tmpl_ids': [(4, self.product_tmpl_a.id)],
            'country_id': self.env.ref('base.pt').id,
            'amount': 12.45,
            'compute_method': 'fixed',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_tmpl_a.product_variant_ids.id,
                'name': self.product_tmpl_a.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice.action_invoice_open()
        invoice_line = invoice.invoice_line_ids[0]
        self.assertEquals(len(invoice_line.tax_fee_ids), 0)
        self.assertFalse(invoice_line.tax_fee_ids)
        self.assertEquals(invoice_line.tax_fee_amount, 0)

    def test_product_multiple_extra_fees(self):
        self.assertFalse(self.product_tmpl_a.tax_fee_ids)
        tax_fee_a = self.env['account.tax.fee'].create({
            'name': 'Ecotax A',
            'apply_on': 'all',
            'country_id': self.env.ref('base.es').id,
            'amount': 10,
            'compute_method': 'fixed',
        })
        tax_fee_b = self.env['account.tax.fee'].create({
            'name': 'Ecotax B',
            'apply_on': 'all',
            'country_id': self.env.ref('base.es').id,
            'amount': 10,
            'compute_method': 'fixed',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product_tmpl_a.product_variant_ids.id,
                    'name': self.product_tmpl_a.name,
                    'account_id': self.account_sale.id,
                    'price_unit': 100,
                    'quantity': 1,
                }),
                (0, 0, {
                    'product_id': self.product_tmpl_b.product_variant_ids.id,
                    'name': self.product_tmpl_b.name,
                    'account_id': self.account_sale.id,
                    'price_unit': 100,
                    'quantity': 1,
                }),
            ],
        })
        invoice.action_invoice_open()
        self.assertEquals(len(invoice.invoice_line_ids), 2)
        for line in invoice.invoice_line_ids:
            self.assertEquals(len(line.tax_fee_ids), 2)
            self.assertEquals(line.tax_fee_amount, 20)
            self.assertEquals(len(line.tax_fee_ids), 2)
            self.assertIn(
                tax_fee_a.id, line.tax_fee_ids.mapped('tax_fee_id').ids)
            self.assertIn(
                tax_fee_b.id, line.tax_fee_ids.mapped('tax_fee_id').ids)
            for tax in line.tax_fee_ids:
                self.assertEquals(tax.tax_fee_amount, 10)

    def test_product_unlink_invoice_lines_and_extra_fees(self):
        self.assertFalse(self.product_tmpl_a.tax_fee_ids)
        tax_fee = self.env['account.tax.fee'].create({
            'name': 'Ecotax A',
            'apply_on': 'all',
            'country_id': self.env.ref('base.es').id,
            'amount': 12.45,
            'compute_method': 'fixed',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_tmpl_a.product_variant_ids.id,
                'name': self.product_tmpl_a.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice_line = invoice.invoice_line_ids[0]
        self.assertEquals(len(invoice_line.tax_fee_ids), 1)
        tax_line = invoice_line.tax_fee_ids
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_amount, 12.45)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_id.id, tax_fee.id)
        self.assertEquals(invoice_line.tax_fee_amount, 12.45)
        invoice.invoice_line_ids.unlink()
        tax_fee_line = self.env['account.tax.fee.line'].search([
            ('id', '=', tax_line.id),
        ])
        self.assertFalse(tax_fee_line)

    def test_product_extra_fees_change_product(self):
        self.assertFalse(self.product_tmpl_a.tax_fee_ids)
        tax_fee = self.env['account.tax.fee'].create({
            'name': 'Ecotax A',
            'apply_on': 'selected_products',
            'product_tmpl_ids': [(6, 0, [self.product_tmpl_a.id])],
            'country_id': self.env.ref('base.es').id,
            'amount': 12.50,
            'compute_method': 'fixed',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_tmpl_a.product_variant_ids.id,
                'name': self.product_tmpl_a.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice_line = invoice.invoice_line_ids[0]
        self.assertEquals(len(invoice_line.tax_fee_ids), 1)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_amount, 12.50)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_id.id, tax_fee.id)
        self.assertEquals(invoice_line.tax_fee_amount, 12.50)
        invoice_line.product_id = self.product_tmpl_b.product_variant_ids.id
        self.assertEquals(len(invoice_line.tax_fee_ids), 0)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_amount, 0)
        self.assertEquals(invoice_line.tax_fee_amount, 0)

    def test_product_extra_fees_change_partner(self):
        self.assertFalse(self.product_tmpl_a.tax_fee_ids)
        tax_fee = self.env['account.tax.fee'].create({
            'name': 'Ecotax A',
            'apply_on': 'selected_products',
            'product_tmpl_ids': [(6, 0, [self.product_tmpl_a.id])],
            'country_id': self.env.ref('base.es').id,
            'amount': 12.50,
            'compute_method': 'fixed',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_tmpl_a.product_variant_ids.id,
                'name': self.product_tmpl_a.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice_line = invoice.invoice_line_ids[0]
        self.assertEquals(len(invoice_line.tax_fee_ids), 1)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_amount, 12.50)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_id.id, tax_fee.id)
        self.assertEquals(invoice_line.tax_fee_amount, 12.50)
        self.partner.country_id = False
        invoice.partner_id = self.partner.id
        self.assertEquals(len(invoice_line.tax_fee_ids), 0)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_amount, 0)
        self.assertEquals(invoice_line.tax_fee_amount, 0)

    def test_product_extra_fees_change_quantity(self):
        self.assertFalse(self.product_tmpl_a.tax_fee_ids)
        tax_fee = self.env['account.tax.fee'].create({
            'name': 'Ecotax A',
            'apply_on': 'selected_products',
            'product_tmpl_ids': [(4, self.product_tmpl_a.id)],
            'country_id': self.env.ref('base.es').id,
            'amount': 12.45,
            'compute_method': 'fixed',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_tmpl_a.product_variant_ids.id,
                'name': self.product_tmpl_a.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice.action_invoice_open()
        invoice_line = invoice.invoice_line_ids[0]
        self.assertEquals(len(invoice_line.tax_fee_ids), 1)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_amount, 12.45)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_id.id, tax_fee.id)
        self.assertEquals(invoice_line.tax_fee_amount, 12.45)
        invoice_line.quantity = 2
        self.assertEquals(invoice_line.tax_fee_amount, 24.9)

    def test_product_extra_fees_sale_workflow(self):
        self.assertFalse(self.product_tmpl_a.tax_fee_ids)
        tax_fee = self.env['account.tax.fee'].create({
            'name': 'Ecotax A',
            'apply_on': 'selected_products',
            'product_tmpl_ids': [(4, self.product_tmpl_a.id)],
            'country_id': self.env.ref('base.es').id,
            'amount': 12.45,
            'compute_method': 'fixed',
        })
        self.product_tmpl_a._compute_tax_fee_ids()
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product_tmpl_a.product_variant_ids.id,
                'product_uom_qty': 1,
                'price_unit': 100,
            })],
        })
        sale_order.action_confirm()
        self.assertEquals(len(sale_order.order_line.tax_fee_ids), 1)
        self.assertEquals(sale_order.order_line.tax_fee_amount, 12.45)
        sale_order.action_invoice_create()
        invoice = sale_order.invoice_ids
        invoice.action_invoice_open()
        invoice_line = invoice.invoice_line_ids[0]
        self.assertEquals(len(invoice_line.tax_fee_ids), 1)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_amount, 12.45)
        self.assertEquals(invoice_line.tax_fee_ids.tax_fee_id.id, tax_fee.id)
        self.assertEquals(invoice_line.tax_fee_amount, 12.45)
