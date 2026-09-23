###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestProjectCurrentBalanceContractLite(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.today = fields.Date.today()
        self.period_start = self.today.replace(day=1)
        self.employee = self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id),
            ('company_id', '=', self.company.id),
        ], limit=1)
        if not self.employee:
            self.employee = self.env['hr.employee'].create({
                'name': 'Contract Employee',
                'user_id': self.env.user.id,
                'company_id': self.company.id,
            })
        self.partner = self.env['res.partner'].create({
            'name': 'Contract Customer',
            'customer_rank': 1,
        })
        self.receivable_account = self.env['account.account'].search([
            ('account_type', '=', 'asset_receivable'),
            ('company_id', 'in', [self.company.id, False]),
            ('deprecated', '=', False),
        ], limit=1)
        self.payable_account = self.env['account.account'].search([
            ('account_type', '=', 'liability_payable'),
            ('company_id', 'in', [self.company.id, False]),
            ('deprecated', '=', False),
        ], limit=1)
        self.income_account = self.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_id', 'in', [self.company.id, False]),
            ('deprecated', '=', False),
        ], limit=1)
        self.journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.company.id),
        ], limit=1)
        self.partner.property_account_receivable_id = self.receivable_account
        self.partner.property_account_payable_id = self.payable_account
        self.product = self.env['product.product'].search([
            ('detailed_type', '=', 'service'),
        ], limit=1)
        if not self.product:
            self.product = self.env['product.product'].search([], limit=1)
        self.contract = self.env['contract_lite.contract'].create({
            'name': 'Maintenance Contract',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'state': 'active',
        })
        self.line = self.env['contract_lite.line'].create({
            'contract_id': self.contract.id,
            'product_id': self.product.id,
            'automatic_price': False,
            'manual_price_unit': 10.0,
            'quantity': 10.0,
            'uom_id': self.product.uom_id.id,
            'name': 'Maintenance service',
            'recurring_interval': 1,
            'recurring_rule_type': 'monthly',
            'date_start': self.period_start,
            'recurring_next_date': self.period_start,
        })
        self.project = self.env['project.project'].create({
            'name': 'Maintenance Project',
            'partner_id': self.partner.id,
            'extra_balance': 5.0,
            'extra_balance_date': self.period_start,
            'contract_lite_line_id': self.line.id,
        })

    def _create_timesheet(self, date, unit_amount):
        return self.env['account.analytic.line'].create({
            'name': 'Timesheet',
            'project_id': self.project.id,
            'date': date,
            'unit_amount': unit_amount,
            'employee_id': self.employee.id,
        })

    def _create_pending_invoice(self, invoice_date=None):
        if invoice_date is None:
            invoice_date = self.today
        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'journal_id': self.journal.id,
            'invoice_date': invoice_date,
            'invoice_line_ids': [(0, 0, {
                'name': 'Maintenance',
                'quantity': 1.0,
                'price_unit': 10.0,
                'account_id': self.income_account.id,
                'contract_lite_line_id': self.line.id,
            })],
        })

    def test_current_balance_uses_contract_balance(self):
        self._create_timesheet(self.period_start + timedelta(days=4), 4.0)
        self.assertEqual(self.project.current_balance, 6.0)

    def test_current_balance_zero_base_with_pending_invoices(self):
        self._create_pending_invoice()
        self._create_timesheet(self.period_start + timedelta(days=4), 4.0)
        self.assertEqual(self.project.current_balance, -4.0)

    def test_future_pending_invoice_does_not_mark_project_as_pending(self):
        self._create_pending_invoice(self.today + timedelta(days=7))
        self._create_timesheet(self.period_start + timedelta(days=4), 4.0)
        self.project._compute_pending_invoices()
        self.project._compute_current_balance()
        self.assertFalse(self.project.has_pending_invoices)
        self.assertEqual(
            self.project.pending_invoices_since, self.today + timedelta(days=7))
        self.assertEqual(self.project.current_balance, 6.0)

    def test_current_balance_falls_back_without_contract_line(self):
        self.project.contract_lite_line_id = False
        self._create_timesheet(self.period_start + timedelta(days=4), 2.0)
        self.assertEqual(self.project.current_balance, 3.0)

    def test_start_date_for_supported_periods(self):
        dayly = self.project._get_start_date('dayly')
        weekly = self.project._get_start_date('weekly')
        monthly = self.project._get_start_date('monthly')
        yearly = self.project._get_start_date('yearly')
        quarterly = self.project._get_start_date('quarterly')
        four_monthly = self.project._get_start_date('four_monthly')
        semesterly = self.project._get_start_date('semesterly')
        self.assertEqual(dayly, self.today)
        self.assertLessEqual(weekly, self.today)
        self.assertEqual(weekly.weekday(), 0)
        self.assertEqual(monthly.day, 1)
        self.assertEqual(yearly.month, 1)
        self.assertIn(quarterly.month, [1, 4, 7, 10])
        self.assertIn(four_monthly.month, [1, 5, 9])
        self.assertIn(semesterly.month, [1, 7])

    def test_weekly_rule_type_is_not_downgraded_to_none(self):
        self.line.recurring_rule_type = 'weekly'
        self.project._compute_renewal_period_lite()
        self.assertEqual(self.project.renewal_period_lite, 'weekly')

    def test_current_balance_uses_weekly_period_start(self):
        self.line.recurring_rule_type = 'weekly'
        self.project._compute_renewal_period_lite()
        week_start = self.project._get_start_date('weekly')
        self._create_timesheet(week_start - timedelta(days=1), 7.0)
        self._create_timesheet(week_start, 3.0)
        self.assertEqual(self.project.current_balance, 7.0)
