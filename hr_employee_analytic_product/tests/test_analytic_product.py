###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAnalyticAccount(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Product = cls.env['product.product']
        cls.product = Product.create({
            'name': 'Normal Product',
            'type': 'service',
            'invoice_policy': 'delivery',
            'service_type': 'timesheet',
            'lst_price': 10,
        })
        cls.employee_product = Product.create({
            'name': 'Employee Product',
            'type': 'service',
            'invoice_policy': 'delivery',
            'service_type': 'timesheet',
            'lst_price': 100,
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Employee Test',
            'product_id': cls.employee_product.id
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Partner Test',
        })
        plan = cls.env['account.analytic.plan'].create({
            'name': 'Account Test',
        })
        account = cls.env['account.analytic.account'].create({
            'name': 'Account Test',
            'plan_id': plan.id,
        })
        cls.project = cls.env['project.project'].create({
            'name': 'Project Test',
            'allow_timesheets': True,
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Task Test',
            'project_id': cls.project.id,
            'timesheet_ids': [(0, 0, {
                'employee_id': cls.employee.id,
                'name': 'Employee Task',
                'unit_amount': 1,
                'account_id': account.id,
            })]
        })

    def test_analytic_account(self):
        wiz = self.env['project.create.sale.order'].with_context({
            'active_ids': [self.project.id],
            'active_id': self.project.id,
            'active_model': 'project.project',
        }).create({
            'partner_id': self.partner.id,
        })
        line = self.env['project.create.sale.order.line'].create({
            'employee_id': self.employee.id,
            'wizard_id': wiz.id,
            'product_id': self.product.id,
        })
        line._onchange_employee_id()
        line._onchange_product_id()
        self.assertEqual(line.product_id, self.employee_product)
        action = wiz.action_create_sale_order()
        sale_order = self.env['sale.order'].browse(action['res_id'])
        order_line = sale_order.order_line
        self.assertEqual(order_line.product_id, self.employee_product)
        self.assertAlmostEqual(
            order_line.price_unit, self.employee_product.lst_price)
        analytic_line = self.env['account.analytic.line'].search([
            ('employee_id', '=', self.employee.id),
        ])
        self.assertEqual(analytic_line, self.task.timesheet_ids)
        self.assertEqual(analytic_line.so_line, order_line)
