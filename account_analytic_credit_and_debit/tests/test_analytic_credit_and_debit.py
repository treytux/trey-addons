###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAnalyticCreditAndDebit(TransactionCase):

    def setUp(self):
        super().setUp()
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'Test Account',
            'plan_id': self.env.ref('analytic.analytic_plan_departments').id,
        })

    def _create_line(self, amount):
        return self.env['account.analytic.line'].create({
            'name': 'Test line',
            'account_id': self.analytic_account.id,
            'amount': amount,
            'date': '2025-01-01',
        })

    def test_positive_amount_goes_to_credit(self):
        line = self._create_line(100.0)
        self.assertEqual(line.debit, 0.0)
        self.assertEqual(line.credit, 100.0)

    def test_negative_amount_goes_to_debit(self):
        line = self._create_line(-50.0)
        self.assertEqual(line.debit, 50.0)
        self.assertEqual(line.credit, 0.0)

    def test_zero_amount_both_zero(self):
        line = self._create_line(0.0)
        self.assertEqual(line.debit, 0.0)
        self.assertEqual(line.credit, 0.0)

    def test_update_positive_to_negative_recomputes(self):
        line = self._create_line(100.0)
        self.assertEqual(line.debit, 0.0)
        self.assertEqual(line.credit, 100.0)
        line.amount = -75.0
        self.assertEqual(line.debit, 75.0)
        self.assertEqual(line.credit, 0.0)

    def test_update_negative_to_positive_recomputes(self):
        line = self._create_line(-200.0)
        self.assertEqual(line.debit, 200.0)
        self.assertEqual(line.credit, 0.0)
        line.amount = 150.0
        self.assertEqual(line.debit, 0.0)
        self.assertEqual(line.credit, 150.0)

    def test_multiple_lines_independent_computation(self):
        lines = self.env['account.analytic.line'].create([
            {'name': 'Line A', 'account_id': self.analytic_account.id,
             'amount': 300.0, 'date': '2025-01-01'},
            {'name': 'Line B', 'account_id': self.analytic_account.id,
             'amount': -120.0, 'date': '2025-01-01'},
            {'name': 'Line C', 'account_id': self.analytic_account.id,
             'amount': 0.0, 'date': '2025-01-01'},
        ])
        self.assertEqual(lines[0].debit, 0.0)
        self.assertEqual(lines[0].credit, 300.0)
        self.assertEqual(lines[1].debit, 120.0)
        self.assertEqual(lines[1].credit, 0.0)
        self.assertEqual(lines[2].debit, 0.0)
        self.assertEqual(lines[2].credit, 0.0)
        self.assertEqual(sum(lines.mapped('debit')), 120.0)
        self.assertEqual(sum(lines.mapped('credit')), 300.0)
