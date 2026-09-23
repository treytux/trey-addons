###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

import odoo.tests
from dateutil.relativedelta import relativedelta
from odoo.tests.common import TransactionCase

from .common import ContractLiteSupplierTestCommonMixin


@odoo.tests.tagged('post_install', '-at_install')
class TestContractLiteSupplier(
        ContractLiteSupplierTestCommonMixin, TransactionCase):
    def setUp(self):
        super().setUp()
        self.today = datetime.now().date()
        self.company = self.env.company
        self._ensure_purchase_journal(self.company)
        self.partner = self.env['res.partner'].create({
            'name': 'Test Vendor',
            'supplier_rank': 1,
        })
        self._ensure_partner_accounts(self.partner, self.company)
        self.product = self._get_test_product()
        self._ensure_expense_account_for_product(self.product, self.company)
        self.contract = self.env['contract_lite_supplier.contract'].create({
            'name': 'Test Supplier Contract',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'state': 'active',
            'code': 'Vendor service #MONTH_STR# #YEAR#',
        })

    def _create_line(self, **overrides):
        date_start = overrides.pop('date_start', self.today)
        recurring_next_date = overrides.pop('recurring_next_date', self.today)
        return self._create_contract_line(
            self.contract,
            self.product,
            date_start=date_start,
            recurring_next_date=recurring_next_date,
            **overrides)

    def test_create_vendor_bills_creates_bill_and_advances_date(self):
        line = self._create_line(
            discount=10.0,
            automatic_price=False,
            price_unit=25.0)
        contract_obj = self.env['contract_lite_supplier.contract']
        moves = contract_obj.cron_create_vendor_bills(
            contracts=self.contract, today=self.today)
        self.assertEqual(len(moves), 1)
        move = moves[0]
        self.assertEqual(move.move_type, 'in_invoice')
        self.assertEqual(move.state, 'draft')
        self.assertEqual(
            move.contract_lite_supplier_contract_id.id, self.contract.id)
        self.assertEqual(move.invoice_date, self.today)
        self.assertEqual(len(move.invoice_line_ids), 1)
        move_line = move.invoice_line_ids[0]
        self.assertEqual(move_line.discount, 10.0)
        self.assertEqual(move_line.price_unit, 25.0)
        self.assertEqual(move_line.contract_lite_supplier_line_id.id, line.id)
        line = self.env['contract_lite_supplier.line'].browse(line.id)
        self.assertEqual(
            line.recurring_next_date, self.today + relativedelta(months=1))

    def test_create_vendor_bills_groups_lines(self):
        line_1 = self._create_line(automatic_price=False, price_unit=10.0)
        line_2 = self._create_line(automatic_price=False, price_unit=20.0)
        contract_obj = self.env['contract_lite_supplier.contract']
        moves = contract_obj.cron_create_vendor_bills(
            contracts=self.contract, today=self.today)
        self.assertEqual(len(moves), 1)
        self.assertEqual(len(moves.invoice_line_ids), 2)
        self.assertEqual(
            moves.invoice_line_ids.contract_lite_supplier_line_id.ids,
            [line_1.id, line_2.id])

    def test_create_vendor_bills_splits_by_next_invoice_date(self):
        yesterday = self.today - timedelta(days=1)
        self._create_line(
            date_start=yesterday,
            recurring_next_date=yesterday,
            automatic_price=False,
            price_unit=10.0)
        self._create_line(
            date_start=self.today,
            recurring_next_date=self.today,
            automatic_price=False,
            price_unit=20.0)
        contract_obj = self.env['contract_lite_supplier.contract']
        moves = contract_obj.cron_create_vendor_bills(
            contracts=self.contract, today=self.today)
        self.assertEqual(len(moves), 2)
        self.assertSetEqual(
            set(moves.mapped('invoice_date')), {yesterday, self.today})

    def test_create_vendor_bills_respects_line_filters(self):
        tomorrow = self.today + timedelta(days=1)
        self._create_line(
            date_start=tomorrow,
            recurring_next_date=self.today,
            automatic_price=False,
            price_unit=10.0)
        self._create_line(
            date_start=self.today,
            recurring_next_date=tomorrow,
            automatic_price=False,
            price_unit=10.0)
        self._create_line(
            date_start=self.today - timedelta(days=2),
            recurring_next_date=self.today,
            date_end=self.today - timedelta(days=1),
            automatic_price=False,
            price_unit=10.0)
        contract_obj = self.env['contract_lite_supplier.contract']
        moves = contract_obj.cron_create_vendor_bills(
            contracts=self.contract, today=self.today)
        self.assertFalse(moves)

    def test_create_vendor_bills_ignores_non_active_contracts(self):
        self.contract.state = 'draft'
        self._create_line(automatic_price=False, price_unit=10.0)
        contract_obj = self.env['contract_lite_supplier.contract']
        moves = contract_obj.cron_create_vendor_bills(
            contracts=self.contract, today=self.today)
        self.assertFalse(moves)

    def test_menu_is_under_payables_and_no_lines_menu(self):
        contracts_menu = self.env.ref(
            'contract_lite_supplier.contract_lite_supplier_menu_contracts')
        payables_menu = self.env.ref('account.menu_finance_payables')
        self.assertEqual(contracts_menu.parent_id.id, payables_menu.id)
        self.assertFalse(
            self.env.ref(
                'contract_lite_supplier.contract_lite_supplier_menu_lines',
                raise_if_not_found=False))
