from odoo.tests.common import TransactionCase


class TestProjectProject(TransactionCase):
    def setUp(self):
        super().setUp()
        self.project_a = self.env.ref('sale_timesheet.project_support')

    def test_01_product_only_project(self):
        self.create_new_project_from_product()
        project = self.env['project.project'].search(
            [], order="create_date desc", limit=1)
        self.assertEqual(project.sale_count, 1)

    def test_02_product_task_global_project(self):
        self.assertEqual(self.project_a.sale_count, 2)
        self.create_new_task_from_product(self.project_a)
        self.project_a._compute_sale_count()
        self.assertEqual(self.project_a.sale_count, 3)
        self.create_new_task_from_product(self.project_a)
        self.project_a._compute_sale_count()
        self.assertEqual(self.project_a.sale_count, 4)

    def create_new_task_from_product(self, project):
        self.service_product = self.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
            'service_tracking': 'task_global_project',
            'project_id': project.id,
            'list_price': 100.0,
            'standard_price': 50.0,
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'state': 'sale',
            'order_line': [(0, 0, {
                'name': 'Test Product',
                'product_id': self.env.ref('product.product_product_4').id,
                'price_unit': 100.0,
            })],
        })
        self.sale_order_line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.service_product.id,
            'name': 'Test Service',
            'price_unit': 100.0,
        })

    def create_new_project_from_product(self):
        self.service_product = self.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
            'service_tracking': 'project_only',
            'list_price': 100.0,
            'standard_price': 50.0,
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'state': 'sale',
            'order_line': [(0, 0, {
                'name': 'Test Product',
                'product_id': self.env.ref('product.product_product_4').id,
                'price_unit': 100.0,
            })],
        })
        self.sale_order_line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.service_product.id,
            'name': 'Test Service',
            'price_unit': 100.0,
        })
