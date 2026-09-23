###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from unittest.mock import patch

from odoo import fields
from odoo.api import call_kw
from odoo.exceptions import ValidationError
from odoo.tests import common


class TestContractInvoiceDateAfterInvoiced(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Skip Condition Partner',
        })
        self.contract = self.env['contract.contract'].create({
            'name': 'Skip Condition Contract',
            'partner_id': self.partner.id,
        })
        self.line_recurrence_contract = self.env['contract.contract'].create({
            'name': 'Line recurrence contract',
            'partner_id': self.partner.id,
            'line_recurrence': True,
        })
        self.product = self.env['product.product'].search([], limit=1)
        if not self.product:
            self.product = self.env['product.product'].create({
                'name': 'Skip Condition Product',
                'type': 'service',
                'sale_line_warn': 'no-message',
                'purchase_line_warn': 'no-message',
            })

    def _create_contract_line(self, contract=None, **extra_values):
        contract = contract or self.contract
        values = {
            'contract_id': contract.id,
            'name': 'Skip Condition Line',
            'product_id': self.product.id,
            'uom_id': self.product.uom_id.id,
            'date_start': '2026-01-01',
            'last_date_invoiced': '2026-01-05',
            'recurring_next_date': '2026-01-10',
            'recurring_rule_type': 'monthly',
            'recurring_interval': 1,
            'recurring_invoicing_type': 'pre-paid',
        }
        values.update(extra_values)
        return self.env['contract.line'].create(values)

    def test_non_cron_path_keeps_date_start_validation(self):
        line = self._create_contract_line(
            contract=self.line_recurrence_contract)
        with self.assertRaises(ValidationError):
            line.write({'date_start': '2026-01-10'})
        with self.assertRaises(ValidationError):
            self._create_contract_line(
                contract=self.line_recurrence_contract,
                date_start='2026-01-10')

    def test_skip_context_bypasses_only_date_start_check(self):
        line = self._create_contract_line(
            contract=self.line_recurrence_contract)
        line.with_context({
            'skip_date_start_last_date_invoiced_check': True}).write({
                'date_start': '2026-01-10',
                'recurring_next_date': '2026-01-10',
            })
        self.assertEqual(
            line.date_start,
            fields.Date.from_string('2026-01-10'))
        with self.assertRaises(ValidationError):
            line.with_context({
                'skip_date_start_last_date_invoiced_check': True}).write({
                    'date_end': '2026-01-03'})
        with self.assertRaises(ValidationError):
            line.with_context({
                'skip_date_start_last_date_invoiced_check': True}).write({
                    'recurring_next_date': '2026-01-03'})

    def test_skip_context_respects_line_recurrence_guard(self):
        line = self._create_contract_line(
            recurring_next_date='2026-01-07')
        line.with_context({
            'skip_date_start_last_date_invoiced_check': True}).write({
                'recurring_next_date': '2026-01-03'})
        self.assertEqual(
            line.recurring_next_date,
            fields.Date.from_string('2026-01-03'))

    def test_cron_recurring_create_invoice_sets_skip_context(self):
        date_ref = fields.Date.from_string('2026-01-31')
        with patch.object(
            type(self.contract), '_cron_recurring_create', autospec=True,
                return_value=True) as mocked_create:
            self.env['contract.contract'].cron_recurring_create_invoice(
                date_ref)
        mocked_self = mocked_create.call_args.args[0]
        self.assertEqual(mocked_create.call_args.args[1], date_ref)
        self.assertEqual(
            mocked_create.call_args.kwargs.get('create_type'),
            'invoice')
        self.assertTrue(
            mocked_self.env.context.get(
                'skip_date_start_last_date_invoiced_check'))

    def test_manual_recurring_create_invoice_sets_skip_context(self):
        def _check_context(recs):
            self.assertTrue(
                recs.env.context.get(
                    'skip_date_start_last_date_invoiced_check'))
            return self.env['account.move']

        with patch.object(
            type(self.contract), '_recurring_create_invoice', autospec=True,
                side_effect=_check_context):
            call_kw(
                self.env['contract.contract'], 'recurring_create_invoice',
                [[self.contract.id]], {})

    def test_manual_recurring_create_invoice_multi_sets_skip_context(self):
        second_contract = self.env['contract.contract'].create({
            'name': 'Second Skip Condition Contract',
            'partner_id': self.partner.id,
        })

        def _check_context(recs):
            self.assertEqual(len(recs), 2)
            self.assertEqual(
                set(recs.ids), {self.contract.id, second_contract.id})
            self.assertTrue(
                recs.env.context.get(
                    'skip_date_start_last_date_invoiced_check'))
            return self.env['account.move']

        with patch.object(
            type(self.contract), '_recurring_create_invoice', autospec=True,
                side_effect=_check_context):
            call_kw(
                self.env['contract.contract'], 'recurring_create_invoice',
                [[self.contract.id, second_contract.id]], {})
