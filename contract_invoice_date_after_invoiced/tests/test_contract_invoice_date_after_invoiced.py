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
        self.product = self.env['product.product'].create({
            'name': 'Skip Condition Product',
            'type': 'service',
        })

    def _create_contract_line(self, vals=None, context=None):
        values = {
            'contract_id': self.contract.id,
            'name': 'Skip Condition Line',
            'product_id': self.product.id,
            'uom_id': self.product.uom_id.id,
            'date_start': '2026-01-01',
            'last_date_invoiced': '2026-01-05',
            'recurring_next_date': '2026-01-10',
        }
        if vals:
            values.update(vals)
        line_model = self.env['contract.line']
        if context:
            line_model = line_model.with_context(context)
        return line_model.create(values)

    def _create_recurring_contract_line(self, vals=None, context=None):
        values = {
            'name': 'Possible line without context',
            'recurring_next_date': '2026-01-11',
            'recurring_rule_type': 'monthly',
            'recurring_interval': 1,
            'recurring_invoicing_type': 'pre-paid',
        }
        if vals:
            values.update(vals)
        return self._create_contract_line(values, context=context)

    def test_contract_line_skip_date_start_last_date_invoiced_check(self):
        line = self._create_contract_line()
        with self.assertRaises(ValidationError):
            line.write({'date_start': '2026-01-10'})
        line.with_context(
            {'skip_date_start_last_date_invoiced_check': True}
        ).write({'date_start': '2026-01-10'})
        self.assertEqual(
            line.date_start,
            fields.Date.from_string('2026-01-10'))
        with self.assertRaises(ValidationError):
            line.with_context(
                {'skip_date_start_last_date_invoiced_check': True}
            ).write({'recurring_next_date': '2026-01-03'})

    def test_cron_recurring_create_invoice_uses_skip_check(self):
        valid_contract_line = self._create_recurring_contract_line()
        with self.assertRaises(ValidationError):
            valid_contract_line.write({'date_start': '2026-01-10'})
        with self.assertRaises(ValidationError):
            self._create_recurring_contract_line({
                'name': 'Impossible line without context',
                'date_start': '2026-01-10',
            })
        invalid_contract_line = self._create_recurring_contract_line(
            vals={
                'name': 'Invalid line kept by cron',
                'date_start': '2026-01-10',
            },
            context={'skip_date_start_last_date_invoiced_check': True})
        self.assertEqual(
            invalid_contract_line.date_start,
            fields.Date.from_string('2026-01-10'))
        self.assertEqual(
            invalid_contract_line.last_date_invoiced,
            fields.Date.from_string('2026-01-05'))
        invoices = self.contract.cron_recurring_create_invoice(
            fields.Date.from_string('2026-01-31'))
        self.assertEqual(len(invoices), 1)
        self.assertTrue(
            invalid_contract_line in invoices.mapped(
                'invoice_line_ids.contract_line_id'))

    def test_manual_recurring_create_invoice_uses_skip_check(self):
        def _check_context(recs, date_ref=False):
            self.assertTrue(
                recs.env.context.get(
                    'skip_date_start_last_date_invoiced_check'))
            self.assertFalse(date_ref)
            return self.env['account.invoice']

        with patch.object(
            type(self.env['contract.contract']), '_recurring_create_invoice',
                autospec=True, side_effect=_check_context):
            call_kw(
                self.env['contract.contract'], 'recurring_create_invoice',
                [[self.contract.id]], {})

    def test_manual_recurring_create_invoice_multi_uses_skip_check(self):
        second_contract = self.env['contract.contract'].create({
            'name': 'Second Skip Condition Contract',
            'partner_id': self.partner.id,
        })

        def _check_context(recs, date_ref=False):
            self.assertEqual(len(recs), 2)
            self.assertEqual(
                set(recs.ids),
                {self.contract.id, second_contract.id})
            self.assertTrue(
                recs.env.context.get(
                    'skip_date_start_last_date_invoiced_check')
            )
            self.assertFalse(date_ref)
            return self.env['account.invoice']

        with patch.object(
            type(self.env['contract.contract']), '_recurring_create_invoice',
                autospec=True, side_effect=_check_context):
            call_kw(
                self.env['contract.contract'], 'recurring_create_invoice',
                [[self.contract.id, second_contract.id]], {})
