###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestSaleOrderLineMaintenanceProduct(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.main_company = self.env.ref('base.main_company')
        self.company_2 = self.env['res.company'].create({
            'name': 'Company 2',
        })
        self.new_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'company_ids': [(6, 0, [self.main_company.id])],
            'company_id': self.main_company.id,
            'groups_id': [(6, 0, [
                self.env.ref('sales_team.group_sale_manager').id,
            ])],
        })
        self.portal_user = self.env['res.users'].create({
            'name': 'Portal User',
            'login': 'portal@test.com',
            'company_ids': [(6, 0, [self.main_company.id])],
            'company_id': self.main_company.id,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_portal').id,
            ])],
        })
        self.new_user.partner_id.email = self.new_user.login
        self.portal_user.partner_id.email = self.portal_user.login
        self.partner = self.env['res.partner'].sudo(
            self.new_user.id).create({
                'name': 'Partner test',
                'company_id': False,
            })
        self.product_tmpl_maintenance = self.env['product.template'].sudo(
            self.new_user.id).create({
                'type': 'service',
                'company_id': False,
                'name': 'Maintenance product',
                'default_code': 'MAINTENANCE',
                'standard_price': 1,
                'list_price': 115,
            })
        self.product_maintenance = (
            self.product_tmpl_maintenance.product_variant_id)
        self.product_01 = self.env['product.product'].sudo(
            self.new_user.id).create({
                'type': 'service',
                'company_id': False,
                'name': 'Service product 1 (with maintenance %)',
                'default_code': 'SERV1',
                'standard_price': 80,
                'list_price': 100,
                'maintenance_percentage': 10,
            })
        self.product_02 = self.env['product.product'].sudo(
            self.new_user.id).create({
                'type': 'service',
                'company_id': False,
                'name': 'Service product 2',
                'default_code': 'SERV2',
                'standard_price': 40,
                'list_price': 50,
            })

    def test_sale_order_without_force_update_maintenance_line(self):
        self.main_company.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        sale_order_obj_website = self.env['sale.order']
        sale = sale_order_obj_website.create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': self.product_02.list_price,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.assertEqual(len(sale.order_line), 3)
        line_product_01 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_01)
        self.assertEqual(line_product_01.product_uom_qty, 1)
        self.assertEqual(line_product_01.price_unit, 100)
        self.assertEqual(line_product_01.price_subtotal, 100)
        self.assertFalse(line_product_01.is_not_increases_maintenance_price)
        line_product_02 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(line_product_02.product_uom_qty, 1)
        self.assertEqual(line_product_02.price_unit, 50)
        self.assertEqual(line_product_02.price_subtotal, 50)
        self.assertTrue(line_product_02.is_not_increases_maintenance_price)
        line_product_maintenance = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(line_product_maintenance.product_uom_qty, 1)
        self.assertEqual(line_product_maintenance.price_unit, 115)
        self.assertEqual(line_product_maintenance.price_subtotal, 115)
        with self.assertRaises(exceptions.UserError) as result:
            line_product_maintenance.order_id = sale.id
        self.assertIn(
            'It is not allowed to modify a maintenance line.',
            result.exception.name)

    def test_sale_order_with_force_update_maintenance_line(self):
        self.main_company.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        self.website = self.env['website'].get_current_website()
        sale_order_obj_website = self.env['sale.order'].with_context(
            website_id=1)
        sale = sale_order_obj_website.create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': self.product_02.list_price,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.assertEqual(len(sale.order_line), 3)
        line_product_01 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_01)
        self.assertEqual(line_product_01.product_uom_qty, 1)
        self.assertEqual(line_product_01.price_unit, 100)
        self.assertEqual(line_product_01.price_subtotal, 100)
        self.assertFalse(line_product_01.is_not_increases_maintenance_price)
        line_product_02 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(line_product_02.product_uom_qty, 1)
        self.assertEqual(line_product_02.price_unit, 50)
        self.assertEqual(line_product_02.price_subtotal, 50)
        self.assertTrue(line_product_02.is_not_increases_maintenance_price)
        line_product_maintenance = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(line_product_maintenance.product_uom_qty, 1)
        self.assertEqual(line_product_maintenance.price_unit, 115)
        self.assertEqual(line_product_maintenance.price_subtotal, 115)
        line_product_maintenance.order_id = sale.id
        self.assertEqual(len(sale.order_line), 3)
