###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderPurchaseOrderLink(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'email': 'customer@customer.com',
        })
        self.project = self.env['project.project'].create({
            'name': "Test Project 1",
            'allow_timesheets': True,
            'partner_id': self.partner.id,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test Journal',
            'code': 'TESTJ',
            'type': 'sale',
        })
        self.contract_template = self.env['contract.template'].create({
            'name': 'Test Contract template',
            'contract_type': 'sale',
            'journal_id': self.journal.id,
        })
        self.service_01 = self.env['product.product'].create({
            'name': "Test Service 1",
            'standard_price': 20.0,
            'list_price': 18.0,
            'type': 'service',
            'default_code': 'SERV1',
            'service_tracking': 'task_global_project',
            'project_id': self.project.id,
            'is_contract': True,
            'recurring_rule_type': 'yearly',
            'property_contract_template_id': self.contract_template.id,
        })
        self.service_02 = self.env['product.product'].create({
            'name': "Test Service 2",
            'standard_price': 30.0,
            'list_price': 22.0,
            'type': 'service',
            'default_code': 'SERV2',
            'service_tracking': 'task_global_project',
            'project_id': self.project.id,
            'is_contract': False,
        })
        self.service_03 = self.env['product.product'].create({
            'name': "Test Service 3",
            'standard_price': 25.0,
            'list_price': 15.0,
            'type': 'service',
            'default_code': 'SERV3',
            'service_tracking': 'no',
            'is_contract': True,
            'recurring_rule_type': 'yearly',
            'property_contract_template_id': self.contract_template.id,
        })

    def test_contract_and_project_from_sale(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.service_01.id,
                    'price_unit': self.service_01.list_price,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEqual(sale.tasks_count, 0)
        self.assertEqual(len(self.project.task_ids), 0)
        sale.action_confirm()
        sale._compute_tasks_ids()
        self.assertEqual(sale.tasks_count, 1)
        self.assertEqual(len(self.project.task_ids), 1)
        contract = self.env['contract.contract'].search([
            ('partner_id', '=', self.partner.id),
        ])
        self.assertEqual(len(contract), 1)
        self.assertEqual(contract.task_count, 1)
        self.assertEqual(
            contract.contract_line_ids.mapped('sale_order_line_id'),
            sale.order_line)
        self.assertEqual(self.project.task_ids.sale_line_id, sale.order_line)

    def test_create_only_project_from_sale(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.service_02.id,
                    'price_unit': self.service_02.list_price,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEqual(sale.tasks_count, 0)
        self.assertEqual(len(self.project.task_ids), 0)
        sale.action_confirm()
        sale._compute_tasks_ids()
        self.assertEqual(sale.tasks_count, 1)
        self.assertEqual(len(self.project.task_ids), 1)
        contract = self.env['contract.contract'].search([
            ('partner_id', '=', self.partner.id),
        ])
        self.assertEqual(len(contract), 0)
        self.assertEqual(contract.task_count, 0)
        self.assertNotEqual(
            contract.contract_line_ids.mapped('sale_order_line_id'),
            sale.order_line)
        self.assertEqual(self.project.task_ids.sale_line_id, sale.order_line)

    def test_create_only_contract_from_sale(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.service_03.id,
                    'price_unit': self.service_03.list_price,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEqual(sale.tasks_count, 0)
        self.assertEqual(len(self.project.task_ids), 0)
        sale.action_confirm()
        sale._compute_tasks_ids()
        self.assertEqual(sale.tasks_count, 0)
        self.assertEqual(len(self.project.task_ids), 0)
        contract = self.env['contract.contract'].search([
            ('partner_id', '=', self.partner.id),
        ])
        self.assertEqual(len(contract), 1)
        self.assertEqual(contract.task_count, 0)
        self.assertEqual(
            contract.contract_line_ids.mapped('sale_order_line_id'),
            sale.order_line)
        self.assertNotEqual(self.project.task_ids.sale_line_id, sale.order_line)
