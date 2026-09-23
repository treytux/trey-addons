###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase


class TestMrpTimesheet(TransactionCase):
    def setUp(self):
        super().setUp()
        self.employee = self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not self.employee:
            self.employee = self.env['hr.employee'].create({
                'name': 'MRP Timesheet Employee',
                'user_id': self.env.user.id,
                'company_id': self.env.company.id,
            })
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'MRP Timesheet Account',
            'plan_id': self.env.company.analytic_plan_id.id,
            'company_id': self.env.company.id,
        })
        self.project = self.env['project.project'].create({
            'name': 'MRP Timesheet Project',
            'analytic_account_id': self.analytic_account.id,
            'allow_timesheets': True,
        })
        self.product = self.env['product.product'].create({
            'name': 'MRP Timesheet Product',
            'type': 'product',
        })
        self.production = self.env['mrp.production'].create({
            'product_id': self.product.id,
            'product_uom_id': self.product.uom_id.id,
            'product_qty': 1.0,
            'analytic_account_id': self.analytic_account.id,
        })

    def test_timesheet_project_matches_production_analytic_account(self):
        self.assertEqual(self.production.timesheet_project_id, self.project)

    def test_create_timesheet_from_production(self):
        timesheet = self.env['account.analytic.line'].create({
            'name': 'Manufacturing work',
            'production_id': self.production.id,
            'project_id': self.production.timesheet_project_id.id,
            'date': fields.Date.today(),
            'unit_amount': 2.5,
            'employee_id': self.employee.id,
        })
        self.assertEqual(timesheet.production_id, self.production)
        self.assertEqual(timesheet.account_id, self.analytic_account)
        self.assertIn(timesheet, self.production.timesheet_ids)
