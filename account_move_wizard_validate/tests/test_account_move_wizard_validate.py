###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests import common


class TestAccountMoveWizardValidate(common.TransactionCase):

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

    def test_account_move_wizard_validate_03(self):
        asset = self.env['account.asset'].create({
            'code': 'CODE-TEST-1234',
            'date_start': fields.Date.today(),
            'method': 'linear',
            'method_period': 'year',
            'method_time': 'year',
            'method_number': 5,
            'name': 'Asset test',
            'profile_id': self.asset_profile.id,
            'purchase_value': 20000,
            'state': 'open',
            'note': 'Notes for asset test',
        })
        self.assertEqual(asset.state, 'open')
        ctx = dict(
            self.env.context, allow_asset=True, check_move_validity=False)
        self.assertEqual(len(asset.depreciation_line_ids), 1)
        line = asset.depreciation_line_ids[0]
        depreciation_date = line.line_date
        am_vals = line._setup_move_data(depreciation_date)
        move = self.env['account.move'].with_context(ctx).create(am_vals)
        depr_acc = asset.profile_id.account_depreciation_id
        exp_acc = asset.profile_id.account_expense_depreciation_id
        aml_d_vals = line._setup_move_line_data(
            depreciation_date, depr_acc, 'depreciation', move)
        self.env['account.move.line'].with_context(ctx).create(aml_d_vals)
        aml_e_vals = line._setup_move_line_data(
            depreciation_date, exp_acc, 'expense', move)
        self.env['account.move.line'].with_context(ctx).create(aml_e_vals)
        line.with_context(allow_asset_line_update=True).write({
            'move_id': move.id,
        })
        wizard = self.env['account.move.wizard.validate'].create({})
        self.assertEqual(wizard.date, fields.Date.today())
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(
            asset.account_move_line_ids.mapped('move_id').state, 'draft')
        wizard.button_accept()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids[0].asset_id, asset)
        self.assertEqual(wizard.line_ids[0].account_move_id, move)
        self.assertEqual(
            asset.account_move_line_ids.mapped('move_id').state, 'posted')
