###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestProjectTaskRealTime(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.analytic_plan = self.env['account.analytic.plan'].create({
            'name': 'Analytic Plan',
        })
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'Analytic Account',
            'plan_id': self.analytic_plan.id,
        })
        self.analytic_line = self.env['account.analytic.line'].create({
            'name': 'Analytic Line',
            'account_id': self.analytic_account.id,
        })

    def test_assign_real_time(self):
        self.analytic_line.write({
            'real_time': 8.0,
        })
        self.assertEqual(self.analytic_line.real_time, 8.0)

    def test_autoassign_real_time(self):
        self.analytic_line.write({
            'unit_amount': 16.0,
        })
        self.analytic_line._onchange_partner_id()
        self.assertEqual(self.analytic_line.real_time, 16.0)
