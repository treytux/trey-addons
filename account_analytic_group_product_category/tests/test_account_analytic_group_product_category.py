###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAccountAnalyticGroupProductCategory(TransactionCase):

    def setUp(self):
        super().setUp()
        self.AnalyticGroup = self.env['account.analytic.group']
        self.AnalyticLine = self.env['account.analytic.line']
        self.ProductCategory = self.env['product.category']
        self.ProductProduct = self.env['product.product']
        self.StockMove = self.env['stock.move']
        self.Plan = self.env['account.analytic.plan']
        self.AnalyticAccount = self.env['account.analytic.account']
        self.group_a = self.AnalyticGroup.create({'name': 'Group A'})
        self.group_b = self.AnalyticGroup.create({'name': 'Group B'})
        self.parent_categ = self.ProductCategory.create({
            'name': 'Parent Category',
            'analytic_group_id': self.group_a.id,
        })
        self.child_categ = self.ProductCategory.create({
            'name': 'Child Category',
            'parent_id': self.parent_categ.id,
        })
        self.categ_without_group = self.ProductCategory.create({
            'name': 'No Group Category',
        })
        self.product_parent = self.ProductProduct.create({
            'name': 'Product in Parent Categ',
            'categ_id': self.parent_categ.id,
            'type': 'product',
        })
        self.product_child = self.ProductProduct.create({
            'name': 'Product in Child Categ',
            'categ_id': self.child_categ.id,
            'type': 'product',
        })
        self.product_no_group = self.ProductProduct.create({
            'name': 'Product without group',
            'categ_id': self.categ_without_group.id,
            'type': 'product',
        })
        plan = self.Plan.create({'name': 'Test Plan'})
        self.analytic_account = self.AnalyticAccount.create({
            'name': 'Test Analytic Account',
            'plan_id': plan.id,
        })

    def _create_analytic_line(self, **kwargs):
        vals = {
            'name': 'Test analytic line',
            'account_id': self.analytic_account.id,
            'amount': 100.0,
        }
        vals.update(kwargs)
        return self.AnalyticLine.create(vals)

    def test_create_sets_group_from_product_category(self):
        line = self._create_analytic_line(product_id=self.product_parent.id)
        self.assertEqual(line.group_id, self.group_a)

    def test_create_no_product_no_group(self):
        line = self._create_analytic_line()
        self.assertFalse(line.group_id)

    def test_create_product_in_category_without_group(self):
        line = self._create_analytic_line(product_id=self.product_no_group.id)
        self.assertFalse(line.group_id)

    def test_hierarchy_fallback_to_parent_category(self):
        line = self._create_analytic_line(product_id=self.product_child.id)
        self.assertEqual(line.group_id, self.group_a)

    def test_hierarchy_overrides_with_direct_category(self):
        self.child_categ.analytic_group_id = self.group_b
        line = self._create_analytic_line(product_id=self.product_child.id)
        self.assertEqual(line.group_id, self.group_b)

    def test_hierarchy_traverses_multiple_levels(self):
        grandchild = self.ProductCategory.create({
            'name': 'Grandchild Category',
            'parent_id': self.child_categ.id,
        })
        product = self.ProductProduct.create({
            'name': 'Product in Grandchild',
            'categ_id': grandchild.id,
            'type': 'product',
        })
        line = self._create_analytic_line(product_id=product.id)
        self.assertEqual(line.group_id, self.group_a)

    def test_write_assigns_group_when_product_changes_to_grouped(self):
        line = self._create_analytic_line(product_id=self.product_no_group.id)
        self.assertFalse(line.group_id)
        line.write({'product_id': self.product_parent.id})
        self.assertEqual(line.group_id, self.group_a)

    def test_write_reassigns_group_when_product_has_new_group(self):
        line = self._create_analytic_line(product_id=self.product_child.id)
        self.assertEqual(line.group_id, self.group_a)
        self.child_categ.analytic_group_id = self.group_b
        line.write({'product_id': self.product_child.id})
        self.assertEqual(line.group_id, self.group_b)

    def test_write_does_not_clear_group_on_ungrouped_product(self):
        line = self._create_analytic_line(product_id=self.product_parent.id)
        self.assertEqual(line.group_id, self.group_a)
        line.write({'product_id': self.product_no_group.id})
        self.assertTrue(line.group_id)

    def test_write_no_change_on_non_product_update(self):
        line = self._create_analytic_line(product_id=self.product_parent.id)
        self.assertEqual(line.group_id, self.group_a)
        line.write({'amount': 999.0})
        self.assertEqual(line.group_id, self.group_a)

    def test_product_for_analytic_group_returns_product(self):
        line = self._create_analytic_line(product_id=self.product_parent.id)
        self.assertEqual(
            line._product_for_analytic_group(), self.product_parent)

    def test_product_for_analytic_group_returns_false(self):
        line = self._create_analytic_line()
        self.assertFalse(line._product_for_analytic_group())

    def test_product_for_analytic_group_requires_single_line(self):
        with self.assertRaises(ValueError) as cm:
            self.AnalyticLine._product_for_analytic_group()
        self.assertIn('Expected singleton', str(cm.exception))

    def test_get_group_direct_category(self):
        line = self._create_analytic_line(product_id=self.product_parent.id)
        group = line._get_group_from_product_category()
        self.assertEqual(group, self.group_a)

    def test_get_group_no_product_no_group(self):
        line = self._create_analytic_line()
        self.assertFalse(line._get_group_from_product_category())

    def test_get_group_no_category_no_group(self):
        line = self._create_analytic_line(product_id=self.product_no_group.id)
        self.assertFalse(line._get_group_from_product_category())

    def test_create_auto_assign_overrides_explicit_group(self):
        line = self._create_analytic_line(
            product_id=self.product_parent.id,
            group_id=self.group_b.id)
        self.assertEqual(line.group_id, self.group_a)

    def test_stock_move_fallback_field_guard(self):
        line = self._create_analytic_line()
        product = line._product_for_analytic_group()
        self.assertFalse(product)

    def test_create_group_as_non_approver_does_not_raise_access_error(self):
        hr_timesheet = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'hr_timesheet'),
            ('state', '=', 'installed'),
        ])
        if not hr_timesheet:
            self.skipTest('hr_timesheet is not installed')
        non_approver = self.env['res.users'].create({
            'name': 'Non Approver Operator',
            'login': 'non_approver_operator@example.com',
            'groups_id': [(6, 0, [
                self.env.ref('analytic.group_analytic_accounting').id,
                self.env.ref('project.group_project_user').id,
            ])],
        })
        line = self.AnalyticLine.with_user(non_approver).create({
            'name': 'Test analytic line',
            'account_id': self.analytic_account.id,
            'amount': 100.0,
            'product_id': self.product_parent.id,
        })
        self.assertEqual(line.group_id, self.group_a)
