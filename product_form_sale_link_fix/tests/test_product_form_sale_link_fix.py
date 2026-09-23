###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo.fields import Datetime
from odoo.tests.common import TransactionCase


class TestProductFormSaleLinkFix(TransactionCase):

    def setUp(self):
        super().setUp()
        self.sales_user = self.env['res.users'].create({
            'name': 'Sales User',
            'login': 'sales_user_test',
            'groups_id': [
                (6, 0, [
                    self.env.ref('sales_team.group_sale_salesman').id,
                    self.env.ref('base.group_user').id,
                ])],
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product for Sales Count',
            'detailed_type': 'consu',
            'list_price': 100.0,
        })
        self.product_template = self.product.product_tmpl_id

    def test_compute_sales_count_within_365_days(self):
        date_recent = Datetime.now() - timedelta(days=10)
        so_recent = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': self.sales_user.id,
            'date_order': date_recent,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5.0,
                'price_unit': 100.0,
            })]
        })
        so_recent.action_confirm()
        self.env.flush_all()
        calculated_sales = self.product.with_user(self.sales_user).sales_count
        self.assertEqual(calculated_sales, 5.0)

    def test_compute_sales_count_outside_365_days(self):
        date_old = Datetime.now() - timedelta(days=400)
        so_old = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': self.sales_user.id,
            'date_order': date_old,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 15.0,
                'price_unit': 100.0,
            })],
        })
        so_old.action_confirm()
        so_old.write({
            'date_order': date_old,
        })
        self.env.flush_all()
        calculated_sales = self.product.with_user(self.sales_user).sales_count
        self.assertEqual(calculated_sales, 0.0)

    def test_action_template_uses_tmpl_id_domain(self):
        if hasattr(self.product_template, 'action_view_sales'):
            action = self.product_template.action_view_sales()
            domain_str = str(action.get('domain', []))
            self.assertIn('product_tmpl_id', domain_str)

    def test_action_variant_uses_product_id_domain(self):
        if hasattr(self.product, 'action_view_sales'):
            action = self.product.action_view_sales()
            domain_str = str(action.get('domain', []))
            self.assertIn('product_id', domain_str)
