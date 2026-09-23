###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAccountFiscalPositionPurchase(TransactionCase):
    def setUp(self):
        super().setUp()

    def create_production(self):
        Product = self.env['product.product']
        Bom = self.env['mrp.bom']
        Line = self.env['mrp.bom.line']
        Production = self.env['mrp.production']
        Workcenter = self.env['mrp.workcenter']
        Workorder = self.env['mrp.workorder']
        Productivity = self.env['mrp.workcenter.productivity']
        Employee = self.env['hr.employee']
        product = Product.create({
            'name': 'Test Product',
            'type': 'product',
        })
        component = Product.create({
            'name': 'Component Product',
            'type': 'product',
        })
        bom = Bom.create({
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_qty': 1,
            'type': 'normal',
        })
        Line.create({
            'bom_id': bom.id,
            'product_id': component.id,
            'product_qty': 1,
        })
        production = Production.create({
            'product_id': product.id,
            'product_qty': 1,
            'product_uom_id': product.uom_id.id,
            'bom_id': bom.id,
        })
        workcenter_id = Workcenter.create({
            'name': 'Test Workcenter',
        })
        workorder_id = Workorder.create({
            'name': 'Test Workorder',
            'production_id': production.id,
            'workcenter_id': workcenter_id.id,
        })
        loss = self.env.ref('mrp.block_reason7')
        Productivity.create({
            'workcenter_id': workcenter_id.id,
            'date_start': '2019-01-01 00:00:00',
            'date_end': '2019-01-01 01:00:00',
            'workorder_id': workorder_id.id,
            'loss_id': loss.id,
        })
        Productivity.create({
            'workcenter_id': workcenter_id.id,
            'date_start': '2019-01-01 04:00:00',
            'date_end': '2019-01-01 06:00:00',
            'workorder_id': workorder_id.id,
            'loss_id': loss.id,
        })
        Employee.create({
            'name': 'Test Employee',
            'timesheet_cost': 10.0,
            'user_id': self.env.user.id,
        })
        return production

    def test_create_analytic_on_finishing_workorders(self):
        """Create analytic lines on finishing work orders """
        production = self.create_production()
        self.assertEqual(production.analytic_line_count, 0)
        account = self.env['account.analytic.account'].create({
            'name': 'Analytic Account',
        })
        production.analytic_account_id = account.id
        self.assertEqual(production.analytic_line_count, 0)
        production.workorder_ids.record_production()
        self.assertEqual(production.analytic_line_count, 2)
        self.assertAlmostEqual(
            sum(production.analytic_line_ids.mapped('amount')), -30.0)

    def test_create_analytic_on_finished_productions(self):
        """Create analytic lines on finished productions """
        production = self.create_production()
        self.assertEqual(production.analytic_line_count, 0)
        production.workorder_ids.time_ids[0].date_end = '2019-01-01 04:47:22'
        production.workorder_ids.time_ids[1].unlink()
        production.workorder_ids.record_production()
        production.workorder_ids.button_start()
        production.button_mark_done()
        self.assertEqual(production.state, 'done')
        self.assertEqual(production.analytic_line_count, 0)
        account = self.env['account.analytic.account'].create({
            'name': 'Analytic Account',
        })
        production.analytic_account_id = account.id
        self.assertEqual(production.analytic_line_count, 1)
        self.assertAlmostEqual(
            sum(production.analytic_line_ids.mapped('amount')), -7.9)
