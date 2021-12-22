###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestProductTemplateProject(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_tmpl = self.env['product.template'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Consu product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.project_1 = self.env['project.project'].create({
            'name': 'Test project 1',
        })
        self.project_2 = self.env['project.project'].create({
            'name': 'Test project 2',
        })

    def test_add_product_to_projects(self):
        self.assertEqual(self.product_tmpl.projects_count, 0)
        self.assertEqual(len(self.project_1.product_tmpl_id), 0)
        self.project_1.product_tmpl_id = self.product_tmpl.id
        self.assertEqual(len(self.project_1.product_tmpl_id), 1)
        self.assertEqual(self.product_tmpl.projects_count, 1)
        self.project_2.product_tmpl_id = self.product_tmpl.id
        self.assertEqual(len(self.project_2.product_tmpl_id), 1)
        self.assertEqual(
            self.product_tmpl.projects_count,
            len(self.product_tmpl.project_ids))
