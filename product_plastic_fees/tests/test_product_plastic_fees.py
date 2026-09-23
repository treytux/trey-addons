###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestProductPlasticFees(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_tmpl = self.env['product.template'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product_tmpl.product_variant_ids.write({
            'plastic_non_recycled_percentage': 50,
            'plastic_weight': 10,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'country_id': self.env.ref('base.es').id,
        })
        type_revenue = self.env.ref('account.data_account_type_revenue')
        type_payable = self.env.ref('account.data_account_type_payable')
        account_obj = self.env['account.account']
        account_customer = account_obj.create({
            'name': 'Customer',
            'code': 'XX_430',
            'user_type_id': type_payable.id,
            'reconcile': True,
        })
        account_supplier = account_obj.create({
            'name': 'Supplier',
            'code': 'XX_400',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.account_sale = account_obj.create({
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

    def test_product_extra_fees_formula_selected_products_plastic(self):
        self.assertFalse(self.product_tmpl.tax_fee_ids)
        self.env['account.tax.fee'].create({
            'name': 'Ecotax formula plastic',
            'apply_on': 'selected_products',
            'product_tmpl_ids': [(4, self.product_tmpl.id)],
            'country_id': self.env.ref('base.es').id,
            'formula': 'result=product_id.plastic_weight_non_recycled*0.45',
            'compute_method': 'formula',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_tmpl.product_variant_ids.id,
                'name': self.product_tmpl.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice.action_invoice_open()
        self.assertEquals(len(invoice.invoice_line_ids[0].tax_fee_ids), 1)
        self.assertEquals(invoice.invoice_line_ids[0].tax_fee_amount, 2.25)

    def test_product_non_plastic_weight(self):
        self.product_tmpl.product_variant_ids.write({
            'plastic_weight': 0,
        })
        self.assertFalse(self.product_tmpl.tax_fee_ids)
        self.env['account.tax.fee'].create({
            'name': 'Ecotax formula plastic',
            'apply_on': 'selected_products',
            'product_tmpl_ids': [(4, self.product_tmpl.id)],
            'country_id': self.env.ref('base.es').id,
            'formula': 'result=product_id.plastic_weight_non_recycled*0.45',
            'compute_method': 'formula',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_tmpl.product_variant_ids.id,
                'name': self.product_tmpl.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice.action_invoice_open()
        self.assertEquals(len(invoice.invoice_line_ids[0].tax_fee_ids), 1)
        self.assertEquals(invoice.invoice_line_ids[0].tax_fee_amount, 0)

    def test_product_non_plastic_percentage(self):
        self.product_tmpl.product_variant_ids.write({
            'plastic_non_recycled_percentage': 0,
        })
        self.assertFalse(self.product_tmpl.tax_fee_ids)
        self.env['account.tax.fee'].create({
            'name': 'Ecotax formula plastic',
            'apply_on': 'selected_products',
            'product_tmpl_ids': [(4, self.product_tmpl.id)],
            'country_id': self.env.ref('base.es').id,
            'formula': 'result=product_id.plastic_weight_non_recycled*0.45',
            'compute_method': 'formula',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_tmpl.product_variant_ids.id,
                'name': self.product_tmpl.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice.action_invoice_open()
        self.assertEquals(len(invoice.invoice_line_ids[0].tax_fee_ids), 1)
        self.assertEquals(invoice.invoice_line_ids[0].tax_fee_amount, 0)
