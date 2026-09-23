###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests import common


class TestAccountAssetMoveCron(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
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
        date_start = fields.Datetime.today() - relativedelta(months=2)
        self.asset = self.env['account.asset'].create({
            'code': 'Test asset v1',
            'purchase_value': 665.0,
            'date_start': date_start,
            'profile_id': self.asset_profile.id,
            'partner_id': self.partner.id,
            'method_time': 'year',
            'method_number': 3,
            'method_period': 'month',
            'method': 'linear',
            'prorata': True,
            'name': 'Asset test',
            'note': 'Notes for asset test',
        })

    def test_account_asset_move_lines_cron_01(self):
        self.assertEqual(self.asset.state, 'draft')
        self.assertEqual(len(self.asset.depreciation_line_ids), 1)
        self.asset.compute_depreciation_board()
        self.assertEqual(len(self.asset.depreciation_line_ids), 38)
        self.asset.validate()
        self.assertEqual(self.asset.state, 'open')
        self.assertFalse(self.asset.depreciation_line_ids[1].move_check)
        self.assertFalse(self.asset.depreciation_line_ids[2].move_check)
        self.env['account.asset.compute'].create({}).asset_compute()
        self.assertTrue(self.asset.depreciation_line_ids[1].move_check)
        self.assertTrue(self.asset.depreciation_line_ids[2].move_check)
        self.assertTrue(self.asset.depreciation_line_ids[1].move_id)
        self.assertTrue(self.asset.depreciation_line_ids[2].move_id)
        self.assertTrue(
            self.asset.depreciation_line_ids[1].line_date < fields.Date.today())
        self.assertTrue(
            self.asset.depreciation_line_ids[2].line_date < fields.Date.today())
        self.assertFalse(self.asset.depreciation_line_ids[3].move_check)
        self.assertFalse(self.asset.depreciation_line_ids[3].move_id)
        self.assertTrue(
            self.asset.depreciation_line_ids[3].line_date > fields.Date.today())
        self.assertFalse(self.asset.depreciation_line_ids[4].move_check)
        self.assertFalse(self.asset.depreciation_line_ids[4].move_id)
        self.assertTrue(
            self.asset.depreciation_line_ids[4].line_date > fields.Date.today())

    def test_account_asset_move_lines_cron_02(self):
        self.assertEqual(len(self.asset.depreciation_line_ids), 1)
        self.asset.compute_depreciation_board()
        self.assertEqual(len(self.asset.depreciation_line_ids), 38)
        self.assertEqual(self.asset.state, 'draft')
        self.assertFalse(self.asset.depreciation_line_ids[1].move_check)
        self.assertFalse(self.asset.depreciation_line_ids[2].move_check)
        self.env['account.asset.compute'].create({}).asset_compute()
        self.assertFalse(self.asset.depreciation_line_ids[1].move_check)
        self.assertFalse(self.asset.depreciation_line_ids[2].move_check)

    def test_account_asset_move_lines_cron_03(self):
        self.asset.date_start = fields.Date.today() + relativedelta(months=1)
        self.assertEqual(len(self.asset.depreciation_line_ids), 1)
        self.asset.compute_depreciation_board()
        self.assertEqual(len(self.asset.depreciation_line_ids), 38)
        self.assertEqual(self.asset.state, 'draft')
        self.assertFalse(self.asset.depreciation_line_ids[1].move_check)
        self.assertFalse(self.asset.depreciation_line_ids[2].move_check)
        self.asset.validate()
        self.assertEqual(self.asset.state, 'open')
        self.env['account.asset.compute'].create({}).asset_compute()
        self.assertFalse(self.asset.depreciation_line_ids[1].move_check)
        self.assertFalse(self.asset.depreciation_line_ids[2].move_check)
