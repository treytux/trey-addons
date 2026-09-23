###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from .common import ContractLiteTestCommonMixin


class TestContractLite(ContractLiteTestCommonMixin, TransactionCase):
    def setUp(self):
        super().setUp()
        self.today = datetime.now().date()
        self.company = self.env.company
        self._ensure_sale_journal(self.company)
        commercial_user = self.env['res.users'].create({
            'name': 'Test user commercial',
            'login': 'commercial_user'
        })
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Test Customer',
            'customer_rank': 1,
            'user_id': commercial_user.id
        })
        self._ensure_partner_accounts(self.partner_01, self.company)
        self.product_01 = self._get_test_product()
        self._ensure_income_account_for_product(self.product_01, self.company)
        self.pricelist_01 = self.env['product.pricelist'].create({
            'name': 'Test Pricelist',
            'currency_id': self.env.ref('base.EUR').id,
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist_01.id,
            'applied_on': '0_product_variant',
            'product_id': self.product_01.id,
            'compute_price': 'fixed',
            'fixed_price': 23.0,
        })
        self.partner_01.property_product_pricelist = self.pricelist_01
        self.contract_01 = self.env['contract_lite.contract'].create({
            'name': 'Test Contract',
            'partner_id': self.partner_01.id,
            'company_id': self.company.id,
            'state': 'active',
            'code': 'Service #MONTH_STR# #YEAR#',
        })

    def _create_line(self, **overrides):
        date_start = overrides.pop('date_start', self.today)
        recurring_next_date = overrides.pop('recurring_next_date', self.today)
        return self._create_contract_line(
            self.contract_01,
            self.product_01,
            date_start=date_start,
            recurring_next_date=recurring_next_date,
            **overrides
        )

    def _try_create_analytic_account(self):
        Analytic = self.env['account.analytic.account']
        vals = {
            'name': 'Test Analytic',
            'company_id': self.company.id,
        }
        if 'plan_id' in Analytic._fields:
            Plan = self.env.get('account.analytic.plan')
            if not Plan:
                return None
            plan = Plan.search([('company_id', '=', self.company.id)], limit=1)
            if not plan:
                plan = Plan.create({
                    'name': 'Test Plan',
                    'company_id': self.company.id,
                })
            vals['plan_id'] = plan.id
        try:
            return Analytic.create(vals)
        except Exception:
            return None

    def test_month_str_is_capitalized(self):
        contract = self.contract_01.with_context(lang='es_ES')
        month = contract._month_str(datetime(2026, 1, 1).date())
        self.assertTrue(month)
        self.assertEqual(month[0], month[0].upper())

    def test_render_invoice_ref_tokens(self):
        contract = self.contract_01.with_context(lang='es_ES')
        contract.code = 'Service #MONTH_INT# #YEAR#'
        ref = contract.render_invoice_ref(datetime(2026, 1, 15).date())
        self.assertIn('01', ref)
        self.assertIn('2026', ref)

    def test_render_invoice_ref_tokens_case_insensitive(self):
        contract = self.contract_01.with_context(lang='es_ES')
        contract.code = 'Service #month_int# #year#'
        ref = contract.render_invoice_ref(datetime(2026, 1, 15).date())
        self.assertIn('01', ref)
        self.assertIn('2026', ref)

    def test_replace_tokens_case_insensitive_and_strip(self):
        contract = self.contract_01
        txt = contract._replace_tokens(
            '  A #month_int# #YEAR#  ',
            {'#MONTH_INT#': '01', '#YEAR#': '2026'},
        )
        self.assertEqual(txt, 'A 01 2026')

    def test_replace_tokens_empty_text_returns_empty(self):
        contract = self.contract_01
        self.assertEqual(contract._replace_tokens('', {'#X#': 'Y'}), '')
        self.assertEqual(contract._replace_tokens(False, {'#X#': 'Y'}), '')

    def test_render_line_description_all_tokens(self):
        contract = self.contract_01.with_context(lang='es_ES')
        date_start = datetime(2026, 1, 1).date()
        date_end = datetime(2026, 1, 31).date()
        rendered = contract.render_line_description(
            '#START#|#END#|#START_MONTH_INT#|#START_YEAR#|'
            '#END_MONTH_INT#|#END_YEAR#',
            date_start,
            date_end,
        )
        self.assertIn('01', rendered)
        self.assertIn('2026', rendered)

    def test_render_line_description_tokens(self):
        line = self._create_line(
            name='X #START_MONTH_INT#/#START_YEAR#'
            ' Y #END_MONTH_INT#/#END_YEAR#'
        ).with_context(lang='es_ES')
        txt = line.render_invoice_line_description(line.recurring_next_date)
        self.assertIn(self.today.strftime('%m/%Y'), txt)
        expected_end = (self.today + relativedelta(months=1)).strftime('%m/%Y')
        self.assertIn(expected_end, txt)

    def test_price_unit_automatic_uses_pricelist(self):
        line = self._create_line(automatic_price=True)
        self.assertEqual(line.price_unit, 23.0)

    def test_price_unit_manual_is_kept_and_stored(self):
        line = self._create_line(
            automatic_price=False,
            price_unit=77.0
        )
        self.assertEqual(line.price_unit, 77.0)
        self.assertEqual(line.manual_price_unit, 77.0)

    def test_price_subtotal_compute(self):
        line = self._create_line(
            automatic_price=False,
            price_unit=10.0,
            quantity=2.0,
            discount=10.0
        )
        self.assertAlmostEqual(line.price_subtotal, 18.0, places=6)

    def test_next_period_date_end_month(self):
        base = datetime(2026, 1, 1).date()
        line = self._create_line(
            date_start=base,
            recurring_next_date=base,
            recurring_rule_type='monthly',
            recurring_interval=1
        )
        self.assertEqual(
            line.next_period_date_end, datetime(2026, 1, 31).date())

    def test_compute_next_date_four_month(self):
        base = datetime(2026, 1, 1).date()
        line = self._create_line(
            date_start=base,
            recurring_next_date=base,
            recurring_rule_type='four_monthly',
            recurring_interval=1
        )
        self.assertEqual(
            line.compute_next_date(base), datetime(2026, 5, 1).date())

    def test_compute_next_date_all_rule_types(self):
        base = datetime(2026, 1, 1).date()
        cases = {
            'dayly': datetime(2026, 1, 2).date(),
            'weekly': datetime(2026, 1, 8).date(),
            'monthly': datetime(2026, 2, 1).date(),
            'quarterly': datetime(2026, 4, 1).date(),
            'four_monthly': datetime(2026, 5, 1).date(),
            'semesterly': datetime(2026, 7, 1).date(),
            'yearly': datetime(2027, 1, 1).date(),
        }
        for rule_type, expected in cases.items():
            line = self._create_line(
                date_start=base,
                recurring_next_date=base,
                recurring_rule_type=rule_type,
                recurring_interval=1,
            )
            self.assertEqual(line.compute_next_date(base), expected)

    def test_compute_portal_dates_from_lines(self):
        self.contract_01.state = 'active'
        self._create_line(
            recurring_next_date=datetime(2026, 1, 1).date(),
            date_end=datetime(2026, 12, 31).date(),
        )
        self._create_line(
            recurring_next_date=datetime(2026, 2, 1).date(),
            date_end=datetime(2026, 10, 31).date(),
        )
        self.contract_01.invalidate_recordset(['line_ids'])
        self.assertEqual(
            self.contract_01.recurring_next_date,
            datetime(2026, 1, 1).date()
        )
        self.assertEqual(self.contract_01.date_end, datetime(2026, 12, 31).date())

    def test_compute_portal_dates_ignores_invalid_next_date(self):
        self._create_line(
            recurring_next_date=datetime(2026, 2, 1).date(),
            date_end=datetime(2026, 1, 31).date(),
        )
        self.contract_01.invalidate_recordset(['line_ids'])
        self.assertFalse(self.contract_01.recurring_next_date)
        self.assertEqual(self.contract_01.date_end, datetime(2026, 1, 31).date())

    def test_compute_access_url(self):
        self.contract_01._compute_access_url()
        self.assertEqual(
            self.contract_01.access_url,
            '/my/contracts-lite/%s' % self.contract_01.id,
        )

    def test_recurring_next_date_uses_manual_value(self):
        manual_date = self.today + relativedelta(days=3)
        line = self._create_line(
            date_start=self.today,
            recurring_next_date=manual_date,
        )
        self.assertEqual(line.recurring_next_date, manual_date)

    def test_create_invoices_respects_start_date(self):
        tomorrow = self.today + timedelta(days=1)
        self._create_line(date_start=tomorrow, recurring_next_date=self.today)
        moves = self.env['contract_lite.contract'].cron_create_invoices(
            contracts=self.contract_01,
            today=self.today
        )
        self.assertFalse(moves)

    def test_create_invoices_respects_next_invoice_date(self):
        tomorrow = self.today + timedelta(days=1)
        self._create_line(date_start=self.today, recurring_next_date=tomorrow)
        moves = self.env['contract_lite.contract'].cron_create_invoices(
            contracts=self.contract_01,
            today=self.today
        )
        self.assertFalse(moves)

    def test_create_invoices_respects_end_date(self):
        yesterday = self.today - timedelta(days=1)
        self._create_line(
            date_start=yesterday,
            recurring_next_date=self.today,
            date_end=yesterday
        )
        moves = self.env['contract_lite.contract'].cron_create_invoices(
            contracts=self.contract_01,
            today=self.today
        )
        self.assertFalse(moves)

    def test_create_invoices_creates_invoice_and_links_and_advances_date(self):
        line = self._create_line(discount=10.0)
        moves = self.env['contract_lite.contract'].cron_create_invoices(
            contracts=self.contract_01,
            today=self.today
        )
        self.assertEqual(len(moves), 1)
        move = moves[0]
        self.assertEqual(
            move.contract_lite_contract_id.id, self.contract_01.id)
        self.assertEqual(move.invoice_date, self.today)
        self.assertTrue(move.ref)
        self.assertEqual(len(move.invoice_line_ids), 1)
        ml = move.invoice_line_ids[0]
        self.assertEqual(ml.discount, 10.0)
        self.assertEqual(ml.price_unit, 23.0)
        self.assertEqual(ml.contract_lite_line_id.id, line.id)
        line = self.env['contract_lite.line'].browse(line.id)
        self.assertEqual(
            line.recurring_next_date,
            self.today + relativedelta(months=1)
        )
        self.assertEqual(
            line.manual_recurring_next_date,
            self.today + relativedelta(months=1)
        )

    def test_create_invoices_groups_lines_in_single_invoice(self):
        line_1 = self._create_line(quantity=2.0)
        line_2 = self._create_line(quantity=3.0)
        moves = self.env['contract_lite.contract'].cron_create_invoices(
            contracts=self.contract_01,
            today=self.today,
        )
        self.assertEqual(len(moves), 1)
        self.assertEqual(len(moves.invoice_line_ids), 2)
        self.assertSetEqual(
            set(moves.invoice_line_ids.mapped('contract_lite_line_id').ids),
            {line_1.id, line_2.id},
        )

    def test_create_invoices_splits_by_recurring_next_date(self):
        yesterday = self.today - timedelta(days=1)
        self._create_line(date_start=yesterday, recurring_next_date=yesterday)
        self._create_line(date_start=self.today, recurring_next_date=self.today)
        moves = self.env['contract_lite.contract'].cron_create_invoices(
            contracts=self.contract_01,
            today=self.today,
        )
        self.assertEqual(len(moves), 2)
        self.assertSetEqual(set(moves.mapped('invoice_date')), {yesterday, self.today})

    def test_create_invoices_ignores_non_active_contracts(self):
        self.contract_01.state = 'draft'
        self._create_line()
        moves = self.env['contract_lite.contract'].cron_create_invoices(
            contracts=self.contract_01,
            today=self.today,
        )
        self.assertFalse(moves)

    def test_create_invoices_respects_contracts_argument(self):
        other_contract = self.env['contract_lite.contract'].create({
            'name': 'Other Contract',
            'partner_id': self.partner_01.id,
            'company_id': self.company.id,
            'state': 'active',
            'code': 'Other #YEAR#',
        })
        self._create_line()
        self.env['contract_lite.line'].create({
            'contract_id': other_contract.id,
            'product_id': self.product_01.id,
            'automatic_price': False,
            'price_unit': 30.0,
            'quantity': 1.0,
            'uom_id': self.product_01.uom_id.id,
            'discount': 0.0,
            'name': 'Other service',
            'recurring_interval': 1,
            'recurring_rule_type': 'monthly',
            'date_start': self.today,
            'recurring_next_date': self.today,
        })
        moves = self.env['contract_lite.contract'].cron_create_invoices(
            contracts=self.contract_01,
            today=self.today,
        )
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves.contract_lite_contract_id.id, self.contract_01.id)

    def test_create_invoices_sets_analytic_distribution_when_possible(self):
        analytic = self._try_create_analytic_account()
        if not analytic:
            return
        self._create_line(analytic_account_id=analytic.id)
        moves = self.env['contract_lite.contract'].cron_create_invoices(
            contracts=self.contract_01,
            today=self.today
        )
        self.assertEqual(len(moves), 1)
        ml = moves.invoice_line_ids[0]
        self.assertTrue(ml.analytic_distribution)
        self.assertIn(analytic.id, ml.analytic_distribution)

    def test_create_invoices_manual_price(self):
        self._create_line(
            automatic_price=False,
            price_unit=77.0
        )
        moves = self.env['contract_lite.contract'].cron_create_invoices(
            contracts=self.contract_01,
            today=self.today
        )
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves.invoice_line_ids[0].price_unit, 77.0)

    def test_invoice_count_compute(self):
        self._create_line()
        self.env['contract_lite.contract'].cron_create_invoices(
            contracts=self.contract_01,
            today=self.today
        )
        self.contract_01 = self.env['contract_lite.contract'].browse(
            self.contract_01.id)
        self.assertGreaterEqual(self.contract_01.invoice_count, 1)

    def test_action_create_invoices_manual_returns_action(self):
        self._create_line()
        action = self.contract_01.action_create_invoices_manual()
        self.assertIn('domain', action)

    def test_action_view_invoices_domain_and_context(self):
        action = self.contract_01.action_view_invoices()
        self.assertEqual(
            action['domain'],
            [
                ('move_type', '=', 'out_invoice'),
                ('contract_lite_contract_id', '=', self.contract_01.id),
            ],
        )
        self.assertEqual(action['context']['default_move_type'], 'out_invoice')
        self.assertEqual(action['context']['default_partner_id'], self.partner_01.id)

    def test_action_view_invoices_includes_only_out_invoice(self):
        self._create_line()
        self.env['contract_lite.contract'].cron_create_invoices(
            contracts=self.contract_01,
            today=self.today,
        )
        refund = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner_01.id,
            'contract_lite_contract_id': self.contract_01.id,
        })
        action = self.contract_01.action_view_invoices()
        domain = action['domain']
        out_invoices = self.env['account.move'].search(domain)
        self.assertTrue(out_invoices)
        self.assertNotIn(refund, out_invoices)

    def test_finish_contract_sets_end_dates_and_closes(self):
        line = self._create_line()
        today = fields.Date.context_today(self.contract_01)
        self.contract_01.action_finish_contract()
        line = self.env['contract_lite.line'].browse(line.id)
        self.contract_01 = self.env['contract_lite.contract'].browse(
            self.contract_01.id)
        self.assertEqual(self.contract_01.state, 'closed')
        self.assertEqual(line.date_end, today)

    def test_action_activate_requires_lines(self):
        contract = self.env['contract_lite.contract'].create({
            'name': 'Empty Contract',
            'partner_id': self.partner_01.id,
            'company_id': self.company.id,
            'state': 'draft',
        })
        with self.assertRaises(UserError):
            contract.action_activate()

    def test_action_set_draft(self):
        self.contract_01.action_set_draft()
        self.contract_01 = self.env['contract_lite.contract'].browse(
            self.contract_01.id)
        self.assertEqual(self.contract_01.state, 'draft')

    def test_check_invoice_user_id(self):
        self._create_line()
        moves = self.env['contract_lite.contract'].cron_create_invoices(
            contracts=self.contract_01,
            today=self.today
        )
        self.assertTrue(moves)
        self.assertEqual(moves.user_id, self.partner_01.user_id)
