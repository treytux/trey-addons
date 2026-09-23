###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAccountAnalyticCostCenter(TransactionCase):

    def setUp(self):
        super().setUp()
        self.cost_center_1 = self.env['account.analytic.cost_center'].create({
            'name': 'Test Cost Center 01',
        })
        self.cost_center_2 = self.env['account.analytic.cost_center'].create({
            'name': 'Test Cost Center 02',
        })
        self.account_customer = self.env['account.account'].create({
            'name': 'Customer',
            'code': '430XXX',
            'account_type': 'asset_receivable',
            'reconcile': True,
        })
        self.account_supplier = self.env['account.account'].create({
            'name': 'Supplier',
            'code': '400XXX',
            'account_type': 'liability_payable',
            'reconcile': True,
        })
        self.account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': '700XXX',
            'account_type': 'income',
            'reconcile': True,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.partner.property_account_receivable_id = self.account_customer.id
        self.partner.property_account_payable_id = self.account_supplier.id
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_account_id': self.account_sale.id,
        })
        self.tax_group_taxes = self.env.ref('account.tax_group_taxes')
        self.tax = self.env['account.tax'].create({
            'name': 'Tax for sale 10%',
            'type_tax_use': 'sale',
            'tax_group_id': self.tax_group_taxes.id,
            'amount_type': 'percent',
            'amount': 10.0,
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
            'taxes_id': [(6, 0, self.tax.ids)],
        })
        self.analytic_account_1 = self.env['account.analytic.account'].create({
            'name': 'Account one',
            'plan_id': self.env.ref('analytic.analytic_plan_departments').id,
        })
        self.analytic_account_2 = self.env['account.analytic.account'].create({
            'name': 'Account two',
            'plan_id': self.env.ref('analytic.analytic_plan_departments').id,
        })

    def test_cost_center_invoice(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'account_id': self.account_sale.id,
                    'price_unit': 100,
                    'quantity': 1,
                    'analytic_distribution_cost_center': {
                        self.analytic_account_1.id: self.cost_center_1.id,
                        self.analytic_account_2.id: self.cost_center_2.id,
                    },
                    'analytic_distribution': {
                        self.analytic_account_1.id: 25,
                        self.analytic_account_2.id: 75,
                    },
                }),
            ],
        })
        invoice.action_post()
        analytic_lines = invoice.line_ids.mapped('analytic_line_ids')
        self.assertTrue(analytic_lines)
        self.assertEqual(len(analytic_lines), 2)
        self.assertEqual(analytic_lines[0].account_id, self.analytic_account_1)
        self.assertEqual(analytic_lines[0].cost_center_id, self.cost_center_1)
        self.assertEqual(analytic_lines[1].account_id, self.analytic_account_2)
        self.assertEqual(analytic_lines[1].cost_center_id, self.cost_center_2)
