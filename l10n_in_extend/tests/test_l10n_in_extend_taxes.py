###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestL10nInExtendTaxes(TransactionCase):

    def setUp(self):
        super().setUp()
        self.main_company = self.env.ref('base.main_company')
        self.india_company = self.env.ref('l10n_in.demo_company_in')
        self.india_chart_template = self.env.ref(
            'l10n_in.indian_chart_template_standard')
        self.custom_tax_templates = self.env['account.tax.template'].search([
            ('chart_template_id', '=', self.india_chart_template.id),
            ('tax_group_id', '=', self.env.ref(
                'l10n_in_extend.india_tax_group').id),
        ])
        generated_taxes = self.custom_tax_templates._generate_tax(
            self.india_company)
        self.tax_template_to_tax = generated_taxes['tax_template_to_tax']
        spanish_country = self.env.ref('base.es')
        india_country = self.env.ref('base.in')
        karnataka_state = self.env.ref('base.state_in_ka')
        self.india_company.state_id = karnataka_state.id
        self.assertEqual(self.india_company.state_id.l10n_in_tin, '29')
        telangana_state = self.env.ref('base.state_in_ts')
        self.partner_spanish = self.env['res.partner'].create({
            'name': 'Test partner spanish',
            'state_id': self.env.ref('base.state_es_bi').id,
            'country_id': spanish_country.id,
        })
        self.partner_india_karnataka = self.env['res.partner'].create({
            'name': 'Test partner India Karnataka',
            'state_id': karnataka_state.id,
            'country_id': india_country.id,
        })
        self.partner_india_telangana = self.env['res.partner'].create({
            'name': 'Test partner India Telangana',
            'state_id': telangana_state.id,
            'country_id': india_country.id,
        })
        self.hs_code_test = self.env['hs.code'].search([], limit=1)
        self.assertTrue(self.hs_code_test)
        self.assertFalse(self.hs_code_test.rate)
        self.product = self.env['product.product'].create({
            'name': 'Test product',
            'type': 'service',
            'company_id': False,
            'hs_code_id': self.hs_code_test.id,
        })
        self.product_without_hs_code = self.env['product.product'].create({
            'name': 'Test Test product without HS Code',
            'type': 'service',
            'company_id': False,
        })
        self.user = self.env['res.users'].create({
            'name': 'Test user',
            'login': 'user@test.com',
            'email': 'user@test.com',
            'company_id': self.main_company.id,
            'company_ids': [
                (6, 0, [self.main_company.id, self.india_company.id]),
            ],
            'groups_id': [(6, 0, [
                self.env.ref('account.group_account_manager').id,
                self.env.ref('base.group_user').id,
                self.env.ref('purchase.group_purchase_manager').id,
                self.env.ref('sales_team.group_sale_manager').id,
            ])],
        })
        self.tax_group_taxes = self.env.ref('account.tax_group_taxes')
        self.tax_sale_main_company = self.env['account.tax'].create({
            'company_id': self.main_company.id,
            'name': 'Tax for sale 21%',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 21,
        })
        self.assertEqual(len(self.tax_sale_main_company), 1)
        self.tax_purchase_main_company = self.env['account.tax'].create({
            'company_id': self.main_company.id,
            'name': 'Tax for purchase 21%',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 21,
        })
        self.assertEqual(len(self.tax_purchase_main_company), 1)
        self.main_income_account = self.env['account.account'].create({
            'code': 'TINC',
            'name': 'Test income account',
            'account_type': 'income',
            'company_id': self.main_company.id,
        })
        self.main_expense_account = self.env['account.account'].create({
            'code': 'TEXP',
            'name': 'Test expense account',
            'account_type': 'expense',
            'company_id': self.main_company.id,
        })
        main_receivable_account = self.env['account.account'].create({
            'code': 'TREC',
            'name': 'Test receivable account',
            'account_type': 'asset_receivable',
            'company_id': self.main_company.id,
        })
        main_payable_account = self.env['account.account'].create({
            'code': 'TPAY',
            'name': 'Test payable account',
            'account_type': 'liability_payable',
            'company_id': self.main_company.id,
        })
        self.partner_spanish.with_company(self.main_company).write({
            'property_account_payable_id': main_payable_account.id,
            'property_account_receivable_id': main_receivable_account.id,
        })
        self.env['account.journal'].create({
            'name': 'Test sale journal',
            'code': 'TSAL',
            'type': 'sale',
            'company_id': self.main_company.id,
        })
        self.env['account.journal'].create({
            'name': 'Test purchase journal',
            'code': 'TPUR',
            'type': 'purchase',
            'company_id': self.main_company.id,
        })
        self.tax_gst_5_sale_india = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'sale'),
        ], limit=1)
        self.assertEqual(len(self.tax_gst_5_sale_india), 1)
        self.tax_gst_5_purchase_india = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'purchase'),
            ('amount', '=', 0.05),
            ('name', 'ilike', 'SGST'),
        ], limit=1)
        self.assertEqual(len(self.tax_gst_5_purchase_india), 1)

    def assign_tax_product_by_company(self, user, product, taxes):
        product.with_user(user).write({
            'taxes_id': [(6, 0, taxes and taxes.ids or [])],
        })

    def create_sale(self, user, partner, product):
        return self.env['sale.order'].with_user(user).create({
            'partner_id': partner.id,
            'company_id': user.company_id.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 1,
                    'product_uom_qty': 1,
                }),
            ],
        })

    def assign_supplier_tax_product_by_company(self, user, product, taxes):
        product.with_company(user.company_id).with_user(user).write({
            'supplier_taxes_id': [(6, 0, taxes and taxes.ids or [])],
        })

    def create_purchase(self, user, partner, product):
        return self.env['purchase.order'].with_user(user).with_company(
            user.company_id).create({
                'partner_id': partner.id,
                'company_id': user.company_id.id,
                'order_line': [
                    (0, 0, {
                        'product_id': product.id,
                        'name': product.name,
                        'price_unit': 1,
                        'product_qty': 1,
                        'product_uom': product.uom_po_id.id,
                    }),
                ],
            })

    def create_invoice(self, user, partner, product, move_type):
        line_values = {
            'product_id': product.id,
            'quantity': 1,
            'price_unit': 1,
        }
        if user.company_id == self.main_company:
            account = (
                self.main_income_account if move_type.startswith('out')
                else self.main_expense_account)
            line_values['account_id'] = account.id
        return self.env['account.move'].with_user(user).with_company(
            user.company_id).create({
                'move_type': move_type,
                'partner_id': partner.id,
                'company_id': user.company_id.id,
                'invoice_line_ids': [(0, 0, line_values)],
            })

    def test_sale_apply_tax_not_india_company(self):
        self.assertEqual(self.user.company_id, self.main_company)
        self.assign_tax_product_by_company(
            self.user, self.product, self.tax_sale_main_company)
        self.product.with_user(self.user)
        self.assertEqual(self.product.taxes_id, self.tax_sale_main_company)
        sale = self.create_sale(self.user, self.partner_spanish, self.product)
        self.assertEqual(sale.company_id, self.main_company)
        self.assertEqual(sale.order_line.tax_id, self.tax_sale_main_company)

    def test_sale_apply_tax_not_india_partner(self):
        self.user.company_id = self.india_company.id
        self.assign_tax_product_by_company(
            self.user, self.product, self.tax_gst_5_sale_india)
        self.product.with_user(self.user)
        self.assertEqual(self.product.taxes_id, self.tax_gst_5_sale_india)
        sale = self.create_sale(self.user, self.partner_spanish, self.product)
        self.assertEqual(sale.company_id, self.india_company)
        self.assertEqual(sale.order_line.tax_id, self.tax_gst_5_sale_india)
        self.assign_tax_product_by_company(self.user, self.product, False)
        self.assertFalse(self.product.taxes_id)
        sale = self.create_sale(self.user, self.partner_spanish, self.product)
        self.assertEqual(sale.company_id, self.india_company)
        self.assertFalse(sale.order_line.tax_id)

    def test_sale_apply_tax_india_same_l10n_in_tin_that_company(self):
        self.user.company_id = self.india_company.id
        self.assertEqual(
            self.partner_india_karnataka.state_id.l10n_in_tin,
            self.india_company.state_id.l10n_in_tin)
        self.assertFalse(self.hs_code_test.rate)
        self.assign_tax_product_by_company(
            self.user, self.product, self.tax_gst_5_sale_india)
        self.product.with_user(self.user)
        self.assertEqual(self.product.taxes_id, self.tax_gst_5_sale_india)
        sale = self.create_sale(
            self.user, self.partner_india_karnataka, self.product)
        self.assertEqual(sale.company_id, self.india_company)
        tax_sgst_0_sale_india = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'sale'),
            ('name', 'ilike', 'SGST'),
            ('name', 'ilike', 'Input'),
            ('amount', '=', 0.0),
        ])
        self.assertEqual(len(tax_sgst_0_sale_india), 1)
        tax_cgst_0_sale_india = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'sale'),
            ('name', 'ilike', 'CGST'),
            ('name', 'ilike', 'Input'),
            ('amount', '=', 0.0),
        ])
        self.assertEqual(len(tax_cgst_0_sale_india), 1)
        self.assertEqual(len(sale.order_line.tax_id), 2)
        self.assertIn(tax_sgst_0_sale_india, sale.order_line.tax_id)
        self.assertIn(tax_cgst_0_sale_india, sale.order_line.tax_id)
        self.hs_code_test.rate = 0.10
        tax_sgst_0_5_sale_india = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'sale'),
            ('name', 'ilike', 'SGST'),
            ('name', 'ilike', 'Input'),
            ('amount', '=', 0.05),
        ])
        self.assertEqual(len(tax_sgst_0_5_sale_india), 1)
        tax_cgst_0_5_sale_india = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'sale'),
            ('name', 'ilike', 'CGST'),
            ('name', 'ilike', 'Input'),
            ('amount', '=', 0.05),
        ])
        self.assertEqual(len(tax_cgst_0_5_sale_india), 1)
        sale = self.create_sale(
            self.user, self.partner_india_karnataka, self.product)
        self.assertEqual(sale.company_id, self.india_company)
        self.assertEqual(len(sale.order_line.tax_id), 2)
        self.assertIn(tax_sgst_0_5_sale_india, sale.order_line.tax_id)
        self.assertIn(tax_cgst_0_5_sale_india, sale.order_line.tax_id)

    def test_sale_apply_tax_india_different_l10n_in_tin_that_company(self):
        self.user.company_id = self.india_company.id
        self.assertNotEqual(
            self.partner_india_telangana.state_id.l10n_in_tin,
            self.india_company.state_id.l10n_in_tin)
        self.assertFalse(self.hs_code_test.rate)
        self.assign_tax_product_by_company(
            self.user, self.product, self.tax_gst_5_sale_india)
        self.product.with_user(self.user)
        self.assertEqual(self.product.taxes_id, self.tax_gst_5_sale_india)
        sale = self.create_sale(
            self.user, self.partner_india_telangana, self.product)
        self.assertEqual(sale.company_id, self.india_company)
        tax_igst_0_sale_india = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'sale'),
            ('name', 'ilike', 'IGST'),
            ('amount', '=', 0),
        ])
        self.assertEqual(len(tax_igst_0_sale_india), 1)
        self.assertEqual(sale.order_line.tax_id, tax_igst_0_sale_india)
        self.hs_code_test.rate = 28
        tax_igst_28_sale_india = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'sale'),
            ('name', 'ilike', 'IGST'),
            ('amount', '=', 28),
        ])
        self.assertEqual(len(tax_igst_28_sale_india), 1)
        sale = self.create_sale(
            self.user, self.partner_india_telangana, self.product)
        self.assertEqual(sale.company_id, self.india_company)
        self.assertEqual(len(sale.order_line.tax_id), 1)
        self.assertIn(tax_igst_28_sale_india, sale.order_line.tax_id)

    def test_sale_apply_tax_india_warning_not_state_company(self):
        self.india_company.state_id = False
        self.user.company_id = self.india_company.id
        with self.assertRaises(exceptions.UserError) as result:
            self.create_sale(
                self.user, self.partner_india_karnataka, self.product)
        self.assertEqual(
            'Please, set state in customer and state in company.',
            result.exception.args[0])

    def test_sale_apply_tax_india_warning_not_state_partner(self):
        self.partner_india_karnataka.state_id = False
        self.user.company_id = self.india_company.id
        with self.assertRaises(exceptions.UserError) as result:
            self.create_sale(
                self.user, self.partner_india_karnataka, self.product)
        self.assertEqual(
            'Please, set state in customer and state in company.',
            result.exception.args[0])

    def test_sale_apply_tax_india_warning_not_hs_code_product(self):
        self.product.hs_code_id = False
        self.user.company_id = self.india_company.id
        with self.assertRaises(exceptions.UserError) as result:
            self.create_sale(
                self.user, self.partner_india_karnataka, self.product)
        self.assertEqual(
            'Please, set HS Code in product.', result.exception.args[0])

    def test_sale_apply_tax_india_hs_code_rate_nil(self):
        self.product.hs_code_id.rate = 'Nil'
        self.user.company_id = self.india_company.id
        self.assign_tax_product_by_company(
            self.user, self.product, self.tax_gst_5_sale_india)
        self.product.with_user(self.user)
        self.assertEqual(self.product.taxes_id, self.tax_gst_5_sale_india)
        sale = self.create_sale(
            self.user, self.partner_india_karnataka, self.product)
        self.assertEqual(sale.company_id, self.india_company)
        self.assertEqual(sale.order_line.tax_id, self.tax_gst_5_sale_india)

    def test_purchase_apply_tax_not_india_company(self):
        self.assertEqual(self.user.company_id, self.main_company)
        self.assign_supplier_tax_product_by_company(
            self.user, self.product, self.tax_purchase_main_company)
        product = self.product.with_company(self.user.company_id)
        self.assertEqual(
            product.supplier_taxes_id, self.tax_purchase_main_company)
        purchase = self.create_purchase(
            self.user, self.partner_spanish, self.product)
        self.assertEqual(purchase.company_id, self.main_company)
        self.assertEqual(
            purchase.order_line.taxes_id, self.tax_purchase_main_company)

    def test_purchase_apply_tax_not_india_vendor(self):
        self.user.company_id = self.india_company.id
        self.assign_supplier_tax_product_by_company(
            self.user, self.product, self.tax_gst_5_purchase_india)
        product = self.product.with_company(self.user.company_id)
        self.assertEqual(
            product.supplier_taxes_id, self.tax_gst_5_purchase_india)
        purchase = self.create_purchase(
            self.user, self.partner_spanish, self.product)
        self.assertEqual(purchase.company_id, self.india_company)
        self.assertEqual(
            purchase.order_line.taxes_id, self.tax_gst_5_purchase_india)
        self.assign_supplier_tax_product_by_company(
            self.user, self.product, False)
        product = self.product.with_company(self.user.company_id)
        self.assertFalse(product.supplier_taxes_id)
        purchase = self.create_purchase(
            self.user, self.partner_spanish, self.product)
        self.assertEqual(purchase.company_id, self.india_company)
        self.assertFalse(purchase.order_line.taxes_id)

    def test_purchase_apply_tax_india_same_l10n_in_tin_that_company(self):
        self.user.company_id = self.india_company.id
        self.assertEqual(
            self.partner_india_karnataka.state_id.l10n_in_tin,
            self.india_company.state_id.l10n_in_tin)
        self.assertFalse(self.hs_code_test.rate)
        self.assign_supplier_tax_product_by_company(
            self.user, self.product, self.tax_gst_5_purchase_india)
        product = self.product.with_company(self.user.company_id)
        self.assertEqual(
            product.supplier_taxes_id, self.tax_gst_5_purchase_india)
        purchase = self.create_purchase(
            self.user, self.partner_india_karnataka, self.product)
        self.assertEqual(purchase.company_id, self.india_company)
        tax_sgst_0_purchase_india = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'purchase'),
            ('name', 'ilike', 'SGST'),
            ('name', 'ilike', 'Output'),
            ('amount', '=', 0.0),
        ])
        self.assertEqual(len(tax_sgst_0_purchase_india), 1)
        tax_cgst_0_purchase_india = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'purchase'),
            ('name', 'ilike', 'CGST'),
            ('name', 'ilike', 'Output'),
            ('amount', '=', 0.0),
        ])
        self.assertEqual(len(tax_cgst_0_purchase_india), 1)
        self.assertEqual(len(purchase.order_line.taxes_id), 2)
        self.assertIn(tax_sgst_0_purchase_india, purchase.order_line.taxes_id)
        self.assertIn(tax_cgst_0_purchase_india, purchase.order_line.taxes_id)
        self.hs_code_test.rate = 0.10
        tax_sgst_0_05_purchase_india = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'purchase'),
            ('name', 'ilike', 'SGST'),
            ('name', 'ilike', 'Output'),
            ('amount', '=', 0.05),
        ])
        self.assertEqual(len(tax_sgst_0_05_purchase_india), 1)
        tax_cgst_0_05_purchase_india = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'purchase'),
            ('name', 'ilike', 'CGST'),
            ('name', 'ilike', 'Output'),
            ('amount', '=', 0.05),
        ])
        self.assertEqual(len(tax_cgst_0_05_purchase_india), 1)
        purchase = self.create_purchase(
            self.user, self.partner_india_karnataka, self.product)
        self.assertEqual(purchase.company_id, self.india_company)
        self.assertEqual(len(purchase.order_line.taxes_id), 2)
        self.assertIn(
            tax_sgst_0_05_purchase_india, purchase.order_line.taxes_id)
        self.assertIn(
            tax_cgst_0_05_purchase_india, purchase.order_line.taxes_id)

    def test_purchase_apply_tax_india_different_l10n_in_tin_that_company(self):
        self.user.company_id = self.india_company.id
        self.assertNotEqual(
            self.partner_india_telangana.state_id.l10n_in_tin,
            self.india_company.state_id.l10n_in_tin)
        self.hs_code_test.rate = 0.08
        self.assign_supplier_tax_product_by_company(
            self.user, self.product, self.tax_gst_5_purchase_india)
        product = self.product.with_company(self.user.company_id)
        self.assertEqual(
            product.supplier_taxes_id, self.tax_gst_5_purchase_india)
        purchase = self.create_purchase(
            self.user, self.partner_india_telangana, self.product)
        self.assertEqual(purchase.company_id, self.india_company)
        tax_igst_0_08_purchase_india = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'purchase'),
            ('name', 'ilike', 'IGST'),
            ('name', 'ilike', 'Output'),
            ('amount', '=', 0.08),
        ])
        self.assertEqual(len(tax_igst_0_08_purchase_india), 1)
        self.assertEqual(len(purchase.order_line.taxes_id), 1)
        self.assertIn(
            tax_igst_0_08_purchase_india, purchase.order_line.taxes_id)

    def test_purchase_apply_tax_india_warning_not_state_company(self):
        self.india_company.state_id = False
        self.user.company_id = self.india_company.id
        with self.assertRaises(exceptions.UserError) as result:
            self.create_purchase(
                self.user, self.partner_india_karnataka, self.product)
        self.assertEqual(
            'Please, set state in vendor and state in company.',
            result.exception.args[0])

    def test_purchase_apply_tax_india_warning_not_state_vendor(self):
        self.partner_india_karnataka.state_id = False
        self.user.company_id = self.india_company.id
        with self.assertRaises(exceptions.UserError) as result:
            self.create_purchase(
                self.user, self.partner_india_karnataka, self.product)
        self.assertEqual(
            'Please, set state in vendor and state in company.',
            result.exception.args[0])

    def test_purchase_apply_tax_india_warning_not_hs_code_product(self):
        self.product.hs_code_id = False
        self.user.company_id = self.india_company.id
        with self.assertRaises(exceptions.UserError) as result:
            self.create_purchase(
                self.user, self.partner_india_karnataka, self.product)
        self.assertEqual(
            'Please, set HS Code in product.', result.exception.args[0])

    def test_purchase_apply_tax_india_hs_code_rate_nil(self):
        self.product.hs_code_id.rate = 'Nil'
        self.user.company_id = self.india_company.id
        self.assign_supplier_tax_product_by_company(
            self.user, self.product, self.tax_gst_5_purchase_india)
        product = self.product.with_company(self.user.company_id)
        self.assertEqual(
            product.supplier_taxes_id, self.tax_gst_5_purchase_india)
        purchase = self.create_purchase(
            self.user, self.partner_india_karnataka, self.product)
        self.assertEqual(purchase.company_id, self.india_company)
        self.assertEqual(
            purchase.order_line.taxes_id, self.tax_gst_5_purchase_india)

    def test_invoice_apply_tax_not_india_company(self):
        self.assertEqual(self.user.company_id, self.main_company)
        self.assign_tax_product_by_company(
            self.user, self.product, self.tax_sale_main_company)
        product = self.product.with_company(self.user.company_id)
        self.assertEqual(
            product.taxes_id, self.tax_sale_main_company)
        invoice = self.create_invoice(
            self.user, self.partner_spanish, self.product, 'out_invoice')
        self.assertEqual(invoice.company_id, self.main_company)
        self.assertEqual(
            invoice.invoice_line_ids.tax_ids, self.tax_sale_main_company)

    def test_invoice_apply_tax_not_india_partner(self):
        self.assign_supplier_tax_product_by_company(
            self.user, self.product, self.tax_purchase_main_company)
        invoice = self.create_invoice(
            self.user, self.partner_spanish, self.product, 'in_invoice')
        self.assertEqual(invoice.company_id, self.main_company)
        self.assertEqual(
            invoice.invoice_line_ids.tax_ids, self.tax_purchase_main_company)

    def test_invoice_keeps_standard_taxes_for_non_indian_partner(self):
        self.user.company_id = self.india_company.id
        self.assign_tax_product_by_company(
            self.user, self.product, self.tax_gst_5_sale_india)
        invoice = self.create_invoice(
            self.user, self.partner_spanish, self.product, 'out_invoice')
        self.assertEqual(
            invoice.invoice_line_ids.tax_ids, self.tax_gst_5_sale_india)
        self.assign_supplier_tax_product_by_company(
            self.user, self.product, self.tax_gst_5_purchase_india)
        invoice_supplier = self.create_invoice(
            self.user, self.partner_spanish, self.product, 'in_invoice')
        self.assertEqual(
            invoice_supplier.invoice_line_ids.tax_ids,
            self.tax_gst_5_purchase_india)

    def test_invoice_applies_same_state_gst_taxes(self):
        self.user.company_id = self.india_company.id
        self.hs_code_test.rate = 0.10
        invoice = self.create_invoice(
            self.user, self.partner_india_karnataka, self.product,
            'out_invoice')
        sale_taxes = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'sale'),
            ('amount', '=', 0.05),
            '|',
            ('name', 'ilike', 'SGST'),
            ('name', 'ilike', 'CGST'),
        ])
        self.assertEqual(invoice.invoice_line_ids.tax_ids, sale_taxes)
        invoice_supplier = self.create_invoice(
            self.user, self.partner_india_karnataka, self.product,
            'in_invoice')
        purchase_taxes = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'purchase'),
            ('amount', '=', 0.05),
            '|',
            ('name', 'ilike', 'SGST'),
            ('name', 'ilike', 'CGST'),
        ])
        self.assertEqual(
            invoice_supplier.invoice_line_ids.tax_ids, purchase_taxes)

    def test_invoice_applies_interstate_igst_tax(self):
        self.user.company_id = self.india_company.id
        self.hs_code_test.rate = 0.08
        invoice = self.create_invoice(
            self.user, self.partner_india_telangana, self.product,
            'out_invoice')
        sale_tax = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'sale'),
            ('amount', '=', 0.08),
            ('name', 'ilike', 'IGST'),
        ])
        self.assertEqual(invoice.invoice_line_ids.tax_ids, sale_tax)
        invoice_supplier = self.create_invoice(
            self.user, self.partner_india_telangana, self.product,
            'in_invoice')
        purchase_tax = self.env['account.tax'].search([
            ('company_id', '=', self.india_company.id),
            ('type_tax_use', '=', 'purchase'),
            ('amount', '=', 0.08),
            ('name', 'ilike', 'IGST'),
        ])
        self.assertEqual(
            invoice_supplier.invoice_line_ids.tax_ids, purchase_tax)

    def test_invoice_requires_customer_state(self):
        self.user.company_id = self.india_company.id
        self.partner_india_karnataka.state_id = False
        with self.assertRaises(exceptions.UserError) as result:
            self.create_invoice(
                self.user, self.partner_india_karnataka, self.product,
                'out_invoice')
        self.assertEqual(
            'Please, set state in customer and state in company.',
            result.exception.args[0])

    def test_invoice_requires_supplier_state(self):
        self.user.company_id = self.india_company.id
        self.partner_india_karnataka.state_id = False
        with self.assertRaises(exceptions.UserError) as result:
            self.create_invoice(
                self.user, self.partner_india_karnataka, self.product,
                'in_invoice')
        self.assertEqual(
            'Please, set state in vendor and state in company.',
            result.exception.args[0])

    def test_invoice_requires_product_hs_code(self):
        self.user.company_id = self.india_company.id
        self.product.hs_code_id = False
        with self.assertRaises(exceptions.UserError) as result:
            self.create_invoice(
                self.user, self.partner_india_karnataka, self.product,
                'out_invoice')
        self.assertEqual(
            'Please, set HS Code in product.', result.exception.args[0])

    def test_invoice_keeps_standard_taxes_for_nil_hs_code_rate(self):
        self.user.company_id = self.india_company.id
        self.hs_code_test.rate = 'Nil'
        self.assign_tax_product_by_company(
            self.user, self.product, self.tax_gst_5_sale_india)
        invoice = self.create_invoice(
            self.user, self.partner_india_karnataka, self.product,
            'out_invoice')
        self.assertEqual(
            invoice.invoice_line_ids.tax_ids, self.tax_gst_5_sale_india)
        self.assign_supplier_tax_product_by_company(
            self.user, self.product, self.tax_gst_5_purchase_india)
        invoice_supplier = self.create_invoice(
            self.user, self.partner_india_karnataka, self.product,
            'in_invoice')
        self.assertEqual(
            invoice_supplier.invoice_line_ids.tax_ids,
            self.tax_gst_5_purchase_india)
