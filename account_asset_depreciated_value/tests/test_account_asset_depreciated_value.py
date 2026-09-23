###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo.tests import common


class TestAccountAssetDepreciatedValue(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        date_start = '07/09/2022'
        date_start = datetime.strptime(date_start, '%d/%m/%Y').date()
        date_end = '01/04/2023'
        date_end = datetime.strptime(date_end, '%d/%m/%Y').date()
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
            'code': 'CODE-ASSET-TEST-1234',
            'purchase_value': 665.0,
            'date_start': date_start,
            'profile_id': self.asset_profile.id,
            'partner_id': self.partner.id,
            'method_time': 'percentage',
            'annual_percentage': 33,
            'method_period': 'month',
            'method': 'linear',
            'prorata': True,
            'name': 'Asset test',
            'note': 'Notes for asset test',
        })
        self.asset_02 = self.env['account.asset'].create({
            'code': 'CODE-ASSET-TEST-1234',
            'purchase_value': 665.0,
            'date_start': date_start,
            'profile_id': self.asset_profile.id,
            'partner_id': self.partner.id,
            'method_time': 'percentage',
            'annual_percentage': 33,
            'method_period': 'month',
            'method': 'linear',
            'prorata': True,
            'name': 'Asset test',
            'value_pending_depreciated': 124.37,
            'date_pending_depreciated': date_end,
            'note': 'Notes for asset test',
        })
        date_start_02 = '13/06/2006'
        date_start_02 = datetime.strptime(date_start_02, '%d/%m/%Y').date()
        self.asset_03 = self.env['account.asset'].create({
            'code': 'CODE-ASSET-TEST-5678',
            'purchase_value': 600.0,
            'date_start': date_start_02,
            'profile_id': self.asset_profile.id,
            'partner_id': self.partner.id,
            'method_time': 'percentage',
            'annual_percentage': 5,
            'method_period': 'month',
            'method': 'linear',
            'prorata': True,
            'name': 'Asset test 3',
            'value_pending_depreciated': 505.00,
            'date_pending_depreciated': date_end,
            'note': 'Notes for asset test 3',
        })

    def to_date(self, date_string):
        return datetime.strptime(date_string, '%Y%m%d').date()

    def test_account_asset_example_01(self):
        self.assertEqual(self.asset_01.state, 'draft')
        self.assertEqual(len(self.asset_01.depreciation_line_ids), 1)
        base_line = self.asset_01.depreciation_line_ids[0]
        self.assertEqual(base_line.type, 'create')
        self.assertEqual(base_line.line_date, self.asset_01.date_start)
        self.assertEqual(base_line.line_days, 0)
        self.assertEqual(base_line.depreciated_value, 0)
        self.assertEqual(base_line.amount, self.asset_01.depreciation_base)
        self.assertEqual(base_line.remaining_value, 0)
        self.asset_01.compute_depreciation_board()
        self.assertEqual(len(self.asset_01.depreciation_line_ids), 38)
        self.asset_01.validate()
        self.assertEqual(self.asset_01.state, 'open')
        first_line = self.asset_01.depreciation_line_ids[1]
        self.assertEqual(first_line.type, 'depreciate')
        self.assertEqual(first_line.line_date, self.to_date('20220930'))
        self.assertEqual(first_line.line_days, 24)
        self.assertEqual(first_line.depreciated_value, 0)
        self.assertEqual(first_line.amount, 14.87)
        self.assertEqual(first_line.remaining_value, 650.13)
        prelast_line = self.asset_01.depreciation_line_ids[36]
        self.assertEqual(prelast_line.type, 'depreciate')
        self.assertEqual(prelast_line.line_date, self.to_date('20250831'))
        self.assertEqual(prelast_line.line_days, 31)
        self.assertEqual(prelast_line.depreciated_value, 636.67)
        self.assertEqual(prelast_line.amount, 18.29)
        self.assertEqual(prelast_line.remaining_value, 10.04)
        last_line = self.asset_01.depreciation_line_ids[37]
        self.assertEqual(last_line.type, 'depreciate')
        self.assertEqual(last_line.line_date, self.to_date('20250930'))
        self.assertEqual(last_line.line_days, 30)
        self.assertEqual(last_line.depreciated_value, 654.96)
        self.assertEqual(last_line.amount, 10.04)
        self.assertEqual(last_line.remaining_value, 0)
        self.assertEqual(self.asset_01.depreciation_base, 665)
        self.assertEqual(self.asset_01.value_residual, 665)
        self.assertEqual(self.asset_01.value_depreciated, 0)
        self.assertEqual(first_line.move_check, False)
        first_line.create_move()
        self.assertEqual(first_line.move_check, True)
        self.assertEqual(self.asset_01.depreciation_base, 665)
        amount = self.asset_01.depreciation_base - first_line.amount
        self.assertEqual(self.asset_01.value_residual, amount)
        self.assertEqual(self.asset_01.value_residual, 650.13)
        self.assertEqual(self.asset_01.value_depreciated, first_line.amount)
        self.assertEqual(self.asset_01.value_depreciated, 14.87)

    def test_account_asset_example_02(self):
        self.assertEqual(
            self.asset_02.date_pending_depreciated, self.to_date('20230401'))
        self.assertEqual(self.asset_02.value_pending_depreciated, 124.37)
        self.assertEqual(self.asset_02.value_residual, 540.63)
        self.assertEqual(self.asset_02.value_depreciated, 124.37)
        self.assertEqual(
            self.asset_02.value_depreciated,
            self.asset_02.value_pending_depreciated)
        self.assertEqual(
            self.asset_02.value_residual,
            self.asset_02.depreciation_base - (
                self.asset_02.value_pending_depreciated))
        self.assertEqual(self.asset_02.state, 'draft')
        self.assertEqual(len(self.asset_02.depreciation_line_ids), 1)
        base_line = self.asset_02.depreciation_line_ids[0]
        self.assertEqual(base_line.type, 'create')
        self.assertEqual(base_line.line_date, self.to_date('20230401'))
        self.assertEqual(base_line.line_days, 0)
        self.assertEqual(
            base_line.depreciated_value, self.asset_02.value_depreciated)
        self.assertEqual(base_line.depreciated_value, 124.37)
        self.assertEqual(base_line.amount, 540.63)
        self.assertEqual(base_line.remaining_value, 0)
        self.asset_02.compute_depreciation_board()
        self.assertEqual(len(self.asset_02.depreciation_line_ids), 31)
        first_line = self.asset_02.depreciation_line_ids[1]
        self.assertEqual(first_line.type, 'depreciate')
        self.assertEqual(first_line.line_date, self.to_date('20230430'))
        self.assertEqual(first_line.line_days, 30)
        self.assertEqual(first_line.depreciated_value, 124.37)
        self.assertEqual(first_line.amount, 18.29)
        self.assertEqual(first_line.remaining_value, 522.34)
        self.assertEqual(len(self.asset_02.depreciation_line_ids), 31)
        prelast_line = self.asset_02.depreciation_line_ids[29]
        self.assertEqual(prelast_line.type, 'depreciate')
        self.assertEqual(prelast_line.line_date, self.to_date('20250831'))
        self.assertEqual(prelast_line.line_days, 31)
        self.assertEqual(prelast_line.depreciated_value, 636.43)
        self.assertEqual(prelast_line.amount, 18.29)
        self.assertEqual(prelast_line.remaining_value, 10.28)
        last_line = self.asset_02.depreciation_line_ids[30]
        self.assertEqual(last_line.type, 'depreciate')
        self.assertEqual(last_line.line_date, self.to_date('20250930'))
        self.assertEqual(last_line.line_days, 30)
        self.assertEqual(last_line.depreciated_value, 654.72)
        self.assertEqual(last_line.amount, 10.28)
        self.assertEqual(last_line.remaining_value, 0)
        self.assertEqual(self.asset_02.depreciation_base, 665)
        self.assertEqual(self.asset_02.value_residual, 540.63)
        self.assertEqual(self.asset_02.value_depreciated, 124.37)
        first_line.create_move()
        self.assertEqual(first_line.move_check, True)
        self.assertEqual(first_line.amount, 18.29)
        self.assertEqual(self.asset_02.depreciation_base, 665)
        self.assertEqual(self.asset_02.value_depreciated, 142.66)
        self.assertEqual(
            self.asset_02.value_depreciated,
            self.asset_02.value_pending_depreciated + first_line.amount)
        self.assertEqual(self.asset_02.value_residual, 522.34)
        depreciated = (
            self.asset_02.value_pending_depreciated + first_line.amount)
        self.assertEqual(
            self.asset_02.value_residual,
            self.asset_02.depreciation_base - depreciated)

    def test_account_asset_example_03(self):
        self.assertEqual(
            self.asset_03.date_pending_depreciated, self.to_date('20230401'))
        self.assertEqual(self.asset_03.value_pending_depreciated, 505.00)
        self.assertEqual(self.asset_03.value_residual, 95.00)
        self.assertEqual(self.asset_03.value_depreciated, 505.00)
        self.assertEqual(
            self.asset_03.value_depreciated,
            self.asset_03.value_pending_depreciated)
        self.assertEqual(
            self.asset_03.value_residual,
            self.asset_03.depreciation_base - (
                self.asset_03.value_pending_depreciated))
        self.assertEqual(self.asset_03.state, 'draft')
        self.assertEqual(len(self.asset_03.depreciation_line_ids), 1)
        base_line = self.asset_03.depreciation_line_ids[0]
        self.assertEqual(base_line.type, 'create')
        self.assertEqual(base_line.line_date, self.to_date('20230401'))
        self.assertEqual(base_line.line_days, 0)
        self.assertEqual(
            base_line.depreciated_value, self.asset_03.value_depreciated)
        self.assertEqual(base_line.depreciated_value, 505.00)
        self.assertEqual(base_line.amount, 95.00)
        self.assertEqual(base_line.remaining_value, 0)
        self.asset_03.compute_depreciation_board()
        self.assertEqual(len(self.asset_03.depreciation_line_ids), 39)
        first_line = self.asset_03.depreciation_line_ids[1]
        self.assertEqual(first_line.type, 'depreciate')
        self.assertEqual(first_line.line_date, self.to_date('20230430'))
        self.assertEqual(first_line.line_days, 30)
        self.assertEqual(first_line.depreciated_value, 505.00)
        self.assertEqual(first_line.amount, 2.50)
        self.assertEqual(first_line.remaining_value, 92.50)
        self.assertEqual(len(self.asset_03.depreciation_line_ids), 39)
        prelast_line = self.asset_03.depreciation_line_ids[37]
        self.assertEqual(prelast_line.type, 'depreciate')
        self.assertEqual(prelast_line.line_date, self.to_date('20260430'))
        self.assertEqual(prelast_line.line_days, 30)
        self.assertEqual(prelast_line.depreciated_value, 595.0)
        self.assertEqual(prelast_line.amount, 2.50)
        self.assertEqual(prelast_line.remaining_value, 2.5)
        last_line = self.asset_03.depreciation_line_ids[38]
        self.assertEqual(last_line.type, 'depreciate')
        self.assertEqual(last_line.line_date, self.to_date('20260531'))
        self.assertEqual(last_line.line_days, 31)
        self.assertEqual(last_line.depreciated_value, 597.50)
        self.assertEqual(last_line.amount, 2.5)
        self.assertEqual(last_line.remaining_value, 0)
        self.assertEqual(self.asset_03.depreciation_base, 600)
        self.assertEqual(self.asset_03.value_residual, 95.00)
        self.assertEqual(self.asset_03.value_depreciated, 505.00)
        first_line.create_move()
        self.assertEqual(first_line.move_check, True)
        self.assertEqual(first_line.amount, 2.50)
        self.assertEqual(self.asset_03.depreciation_base, 600)
        self.assertEqual(self.asset_03.value_depreciated, 507.50)
        self.assertEqual(
            self.asset_03.value_depreciated,
            self.asset_03.value_pending_depreciated + first_line.amount)
        self.assertEqual(self.asset_03.value_residual, 92.5)
        depreciated = (
            self.asset_03.value_pending_depreciated + first_line.amount)
        self.assertEqual(
            self.asset_03.value_residual,
            self.asset_03.depreciation_base - depreciated)
