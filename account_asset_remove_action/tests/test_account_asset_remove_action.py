###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions, fields
from odoo.tests import common


class TestAccountAssetRemoveAction(common.TransactionCase):
    def setUp(self):
        super().setUp()
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
        self.asset_01 = self.env['account.asset'].create({
            'name': 'Asset test 1',
            'code': 'CODE-TEST-1234',
            'profile_id': self.asset_profile.id,
            'purchase_value': 5000,
            'salvage_value': 0,
            'date_start': '2019-01-01',
            'method': 'linear',
            'method_time': 'year',
            'method_number': 5,
            'method_period': 'year',
            'prorata': False,
            'note': 'Notes for asset test 1',
        })
        self.asset_02 = self.env['account.asset'].create({
            'name': 'Asset test 2',
            'code': 'CODE-TEST-5678',
            'profile_id': self.asset_profile.id,
            'purchase_value': 10000,
            'salvage_value': 0,
            'date_start': '2019-01-01',
            'method': 'linear',
            'method_time': 'year',
            'method_number': 5,
            'method_period': 'year',
            'prorata': False,
            'note': 'Notes for asset test 2',
        })

    def test_remove_assets_from_tree_view_ok(self):
        self.assertEqual(self.asset_01.state, 'draft')
        self.assertEqual(self.asset_02.state, 'draft')
        self.asset_01.compute_depreciation_board()
        self.asset_02.compute_depreciation_board()
        self.asset_01.validate()
        self.asset_02.validate()
        self.assertEqual(self.asset_01.state, 'open')
        self.assertEqual(self.asset_02.state, 'open')
        account_sale = self.env['account.account'].search([
            ('code', '=', '200000'),
        ])
        account_expense = self.env['account.account'].create({
            'name': 'Expenses test',
            'code': 'XTEST',
            'user_type_id': self.env.ref(
                'account.data_account_type_expenses').id,
        })
        wizard = self.env['account.asset.remove.multiple'].with_context(
            active_ids=[self.asset_01.id, self.asset_02.id]).create({
                'date_remove': '2019-01-31',
                'sale_value': 0.0,
                'posting_regime': 'gain_loss_on_sale',
                'account_plus_value_id': account_sale.id,
                'account_min_value_id': account_expense.id,
            })
        wizard.button_accept()
        self.asset_01.refresh()
        self.asset_02.refresh()
        self.assertEqual(self.asset_01.state, 'removed')
        self.assertEqual(self.asset_02.state, 'removed')

    def test_remove_assets_from_tree_view_error(self):
        self.assertEqual(self.asset_01.state, 'draft')
        self.assertEqual(self.asset_02.state, 'draft')
        self.asset_01.compute_depreciation_board()
        self.asset_02.compute_depreciation_board()
        self.asset_01.validate()
        self.asset_02.validate()
        self.assertEqual(self.asset_01.state, 'open')
        self.assertEqual(self.asset_02.state, 'open')
        account_sale = self.env['account.account'].search([
            ('code', '=', '200000'),
        ])
        account_expense = self.env['account.account'].create({
            'name': 'Expenses test',
            'code': 'XTEST',
            'user_type_id': self.env.ref(
                'account.data_account_type_expenses').id,
        })
        wizard = self.env['account.asset.remove.multiple'].with_context(
            active_ids=[self.asset_01.id, self.asset_02.id]).create({
                'date_remove': fields.Date.today(),
                'sale_value': 0.0,
                'posting_regime': 'gain_loss_on_sale',
                'account_plus_value_id': account_sale.id,
                'account_min_value_id': account_expense.id,
            })
        with self.assertRaises(exceptions.UserError) as result:
            wizard.button_accept()
        self.assertEqual(
            result.exception.name,
            "You can't make an early removal if all the depreciation "
            "lines for previous periods are not posted."
        )
