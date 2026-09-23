###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestAccountAnalyticLineProjectWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Customer Test',
            'is_company': True,
            'customer_rank': 1,
        })
        self.income_account = self.env['account.account'].create({
            'name': 'Test income',
            'code': '700999',
            'account_type': 'income',
            'company_id': self.env.company.id,
        })
        self.product_category = self.env['product.category'].create({
            'name': 'Service category',
        })
        if 'property_account_income_categ_id' in self.product_category._fields:
            self.product_category.property_account_income_categ_id = (
                self.income_account.id
            )
        self.product = self.env['product.product'].create({
            'name': 'Service product',
            'type': 'service',
            'categ_id': self.product_category.id,
            'list_price': 100.0,
            'standard_price': 40.0,
            'company_id': False,
        })
        self.analytic_plan = self.env.ref('analytic.analytic_plan_departments')
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'Analytic account test',
            'plan_id': self.analytic_plan.id,
        })
        self.project = self.env['project.project'].create({
            'name': 'Project test',
            'analytic_account_id': self.analytic_account.id,
        })
        self.task = self.env['project.task'].create({
            'name': 'Task test',
            'project_id': self.project.id,
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Employee test',
            'user_id': self.env.user.id,
            'company_id': self.env.company.id,
        })

    def _create_analytic_line(self, amount, **kwargs):
        values = {
            'name': 'Analytic line test',
            'date': fields.Date.today(),
            'account_id': self.analytic_account.id,
            'unit_amount': 2.0,
            'amount': amount,
            'employee_id': self.employee.id,
        }
        values.update(kwargs)
        return self.env['account.analytic.line'].create(values)

    def _get_wizard(self, lines):
        return self.env['analytic.create.invoice'].with_context(
            active_ids=lines.ids
        ).create({})

    def _create_settlement(self):
        partner_fields = self.env['res.partner']._fields
        values = {'name': 'Agent Test'}
        if 'agent' not in partner_fields:
            self.skipTest('Agent fields are not installed.')
        values.update({
            'agent': True,
            'agent_type': 'agent',
            'settlement': 'monthly',
        })
        agent_partner = self.env['res.partner'].create(values)
        return self.env['sale.commission.settlement'].create({
            'agent_id': agent_partner.id,
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today(),
            'company_id': self.env.company.id,
        })

    def test_create_invoice_marks_analytic_line_as_invoiced(self):
        line = self._create_analytic_line(
            -50.0, project_id=self.project.id, task_id=self.task.id,
            partner_id=self.partner.id, product_id=self.product.id)
        self.assertEqual(line.task_state, 'to_invoice')
        wizard = self._get_wizard(line)
        invoice = wizard.create_invoice()
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids.product_id, self.product)
        self.assertEqual(invoice.invoice_line_ids.quantity, 2.0)
        if 'task_id' in self.env['account.move.line']._fields:
            self.assertEqual(invoice.invoice_line_ids[0].task_id, self.task)
        self.assertEqual(line.task_invoice_id, invoice)
        self.assertEqual(line.task_state, 'invoiced')

    def test_create_sale_order_marks_analytic_line_as_invoiced(self):
        line = self._create_analytic_line(
            -80.0, project_id=self.project.id, task_id=self.task.id,
            partner_id=self.partner.id, product_id=self.product.id
        )
        wizard = self._get_wizard(line)
        wizard.create_sale_order()
        sale = self.env['sale.order'].search([
            ('partner_id', '=', self.partner.id),
            ('analytic_account_id', '=', self.analytic_account.id),
        ], limit=1)
        self.assertTrue(sale)
        self.assertEqual(sale.partner_id, self.partner)
        self.assertEqual(sale.analytic_account_id, self.analytic_account)
        self.assertEqual(len(sale.order_line), 1)
        self.assertEqual(sale.order_line.product_id, self.product)
        if 'timesheet_ids' in self.env['sale.order.line']._fields:
            self.assertEqual(sale.order_line[0].timesheet_ids, line)
        elif 'analytic_line_ids' in self.env['sale.order.line']._fields:
            self.assertEqual(sale.order_line[0].analytic_line_ids, line)
        self.assertEqual(line.task_state, 'invoiced')

    def test_create_invoice_and_open_returns_invoice_action(self):
        line = self._create_analytic_line(
            -60.0, project_id=self.project.id, task_id=self.task.id,
            partner_id=self.partner.id, product_id=self.product.id
        )
        action = self._get_wizard(line).create_invoice_and_open()
        self.assertEqual(action['res_id'], line.task_invoice_id.id)
        self.assertEqual(action['res_model'], 'account.move')
        self.assertTrue(action['views'])

    def test_grouped_invoicing_by_product(self):
        line_1 = self._create_analytic_line(
            -30.0, project_id=self.project.id, task_id=self.task.id,
            partner_id=self.partner.id, product_id=self.product.id,
            name='First line', unit_amount=1.0)
        line_2 = self._create_analytic_line(
            -70.0, project_id=self.project.id, task_id=self.task.id,
            partner_id=self.partner.id, product_id=self.product.id,
            name='Second line', unit_amount=3.0)
        wizard = self._get_wizard(line_1 | line_2)
        wizard.product_group = True
        invoice = wizard.create_invoice()
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids.product_id, self.product)
        self.assertEqual(invoice.invoice_line_ids.quantity, 4.0)
        self.assertEqual(set(invoice.invoice_line_ids.analytic_line_ids.ids), {
            line_1.id,
            line_2.id,
        })
        self.assertEqual(line_1.task_state, 'invoiced')
        self.assertEqual(line_2.task_state, 'invoiced')

    def test_force_product_overrides_missing_product(self):
        line = self._create_analytic_line(
            -45.0, project_id=self.project.id, task_id=self.task.id,
            partner_id=self.partner.id, product_id=False)
        wizard = self._get_wizard(line)
        wizard.force_product = True
        wizard.product_id = self.product
        invoice = wizard.create_invoice()
        self.assertEqual(invoice.invoice_line_ids.product_id, self.product)
        self.assertEqual(line.task_state, 'invoiced')

    def test_rejects_multiple_partners(self):
        other_partner = self.env['res.partner'].create({
            'name': 'Customer Other',
            'is_company': True,
            'customer_rank': 1,
        })
        line_1 = self._create_analytic_line(
            -20.0, project_id=self.project.id, task_id=self.task.id,
            partner_id=self.partner.id, product_id=self.product.id)
        line_2 = self._create_analytic_line(
            -20.0, project_id=self.project.id, task_id=self.task.id,
            partner_id=other_partner.id, product_id=self.product.id)
        wizard = self._get_wizard(line_1 | line_2)
        with self.assertRaises(ValidationError):
            wizard.create_invoice()

    def test_rejects_missing_product(self):
        line = self._create_analytic_line(
            -15.0, project_id=self.project.id, task_id=self.task.id,
            partner_id=self.partner.id, product_id=False)
        wizard = self._get_wizard(line)
        with self.assertRaises(ValidationError):
            wizard.create_invoice()

    def test_rejects_missing_task(self):
        line = self._create_analytic_line(
            -15.0, project_id=self.project.id, partner_id=self.partner.id,
            product_id=self.product.id)
        wizard = self._get_wizard(line)
        with self.assertRaises(ValidationError):
            wizard.create_invoice()

    def test_task_state_resync_on_write(self):
        line = self._create_analytic_line(
            -10.0, project_id=self.project.id, task_id=self.task.id,
            partner_id=self.partner.id, product_id=self.product.id)
        self.assertEqual(line.task_state, 'to_invoice')
        line.write({
            'amount': 10.0,
        })
        self.assertEqual(line.task_state, 'not_billable')
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })
        line.write({
            'task_invoice_id': invoice.id,
        })
        self.assertEqual(line.task_state, 'invoiced')
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        sale_line = self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': self.product.id,
            'name': self.product.name,
            'product_uom_qty': 1.0,
            'price_unit': self.product.list_price,
        })
        line.write({
            'so_line': sale_line.id,
        })
        self.assertEqual(line.task_state, 'invoiced')

        settlement = self._create_settlement()
        line.write({
            'settlement_id': settlement.id,
        })
        self.assertEqual(line.task_state, 'settled')

    def test_rejects_non_billable_lines(self):
        line = self._create_analytic_line(
            -10.0, project_id=self.project.id, task_id=self.task.id,
            partner_id=self.partner.id, product_id=self.product.id)
        line.write({
            'amount': 50.0,
        })
        self.assertEqual(line.task_state, 'not_billable')
        wizard = self._get_wizard(line)
        with self.assertRaises(ValidationError):
            wizard.create_invoice()
