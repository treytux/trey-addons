###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestAccountAssetCodeInvoice(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.type_recv = self.env.ref('account.data_account_type_receivable')
        self.type_payable = self.env.ref('account.data_account_type_payable')
        self.account_payable = self.env['account.account'].create({
            'name': 'test_account_payable',
            'code': '321',
            'user_type_id': self.type_payable.id,
            'company_id': self.env.user.company_id.id,
            'reconcile': True,
        })
        self.account_recv = self.env['account.account'].create({
            'name': 'test_account_receivable',
            'code': '123',
            'user_type_id': self.type_recv.id,
            'company_id': self.env.user.company_id.id,
            'reconcile': True,
        })
        self.account_expense = self.env['account.account'].create({
            'code': 'X2120',
            'name': 'Expenses test',
            'user_type_id': self.env.ref(
                'account.data_account_type_expenses').id,
        })
        self.account_xfa = self.env['account.account'].create({
            'code': 'X1000',
            'name': 'Fixed assets tests',
            'user_type_id': self.env.ref(
                'account.data_account_type_fixed_assets').id,
        })
        self.expenses_journal = self.env['account.journal'].create({
            'name': 'Vendor bills test',
            'code': 'TEXJ',
            'type': 'purchase',
            'default_debit_account_id': self.account_expense.id,
            'default_credit_account_id': self.account_expense.id,
            'refund_sequence': True,
        })
        self.asset_profile = self.env['account.asset.profile'].create({
            'account_expense_depreciation_id': self.account_expense.id,
            'account_asset_id': self.account_xfa.id,
            'account_depreciation_id': self.account_xfa.id,
            'journal_id': self.expenses_journal.id,
            'name': 'Test profile',
            'method_time': 'year',
            'method_number': 5,
            'method_period': 'year',
        })
        self.product = self.env.ref('product.product_product_4')
        self.invoice_line = self.env['account.invoice.line'].create({
            'name': 'test',
            'account_id': self.account_payable.id,
            'price_unit': 2000.00,
            'quantity': 1,
            'product_id': self.product.id,
        })
        self.partner = self.env.ref('base.res_partner_2')
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'account_id': self.account_recv.id,
            'journal_id': self.expenses_journal.id,
            'invoice_line_ids': [
                (4, self.invoice_line.id),
            ],
        })

    def test_create_asset_from_invoice_01(self):
        self.assertFalse(self.invoice.number)
        all_asset = self.env['account.asset'].search([])
        asset_profile = self.asset_profile
        asset_profile.asset_product_item = False
        self.assertEqual(len(self.invoice.invoice_line_ids), 1)
        line = self.invoice.invoice_line_ids[0]
        self.assertTrue(line.price_unit > 0.0)
        line.asset_profile_id = asset_profile
        self.invoice.action_invoice_open()
        self.assertTrue(self.invoice.number)
        current_asset = self.env['account.asset'].search([])
        new_asset = current_asset - all_asset
        self.assertEqual(len(new_asset), 1)
        self.assertTrue(new_asset.code)
        self.assertEqual(
            new_asset.code,
            '%s-%s' % (self.invoice.number, self.invoice_line.id))
        self.assertFalse(new_asset.profile_id.open_asset)
        self.assertEqual(new_asset.state, 'draft')
        self.assertEqual(len(new_asset.depreciation_line_ids), 1)
        new_asset.compute_depreciation_board()
        self.assertTrue(len(new_asset.depreciation_line_ids) > 1)
        self.assertFalse(new_asset.depreciation_line_ids[1].move_id)
        new_asset.depreciation_line_ids[1].create_move()
        self.assertTrue(new_asset.depreciation_line_ids[1].move_id)
        self.assertEqual(
            new_asset.depreciation_line_ids[1].move_id.ref,
            '%s/%s' % (new_asset.code, 1))

    def test_create_asset_from_invoice_02(self):
        self.assertFalse(self.asset_profile.open_asset)
        self.asset_profile.open_asset = True
        self.assertTrue(self.asset_profile.open_asset)
        self.assertFalse(self.invoice.number)
        all_asset = self.env['account.asset'].search([])
        asset_profile = self.asset_profile
        asset_profile.asset_product_item = False
        self.assertEqual(len(self.invoice.invoice_line_ids), 1)
        line = self.invoice.invoice_line_ids[0]
        self.assertTrue(line.price_unit > 0.0)
        line.asset_profile_id = asset_profile
        self.invoice.action_invoice_open()
        self.assertTrue(self.invoice.number)
        current_asset = self.env['account.asset'].search([])
        new_asset = current_asset - all_asset
        self.assertEqual(len(new_asset), 1)
        self.assertTrue(new_asset.code)
        self.assertEqual(
            new_asset.code,
            '%s-%s' % (self.invoice.number, self.invoice_line.id))
        self.assertTrue(new_asset.profile_id.open_asset)
        self.assertEqual(new_asset.state, 'open')
        self.assertTrue(len(new_asset.depreciation_line_ids) > 1)
        self.assertFalse(new_asset.depreciation_line_ids[1].move_id)
        new_asset.depreciation_line_ids[1].create_move()
        self.assertTrue(new_asset.depreciation_line_ids[1].move_id)
        self.assertEqual(
            new_asset.depreciation_line_ids[1].move_id.ref,
            '%s/%s' % (new_asset.code, 1))
