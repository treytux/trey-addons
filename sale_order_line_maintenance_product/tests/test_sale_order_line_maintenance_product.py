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
        self.new_user.partner_id.email = self.new_user.login
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

    def test_sale_order_line_less_maintenance_price(self):
        self.main_company.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        sale = self.env['sale.order'].sudo(
            self.new_user.id).create({
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
        self.assertEqual(len(sale.order_line), 4)
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
        self.assertTrue(
            line_product_maintenance.is_not_increases_maintenance_price)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t1.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)

    def test_sale_order_line_greater_maintenance_price(self):
        self.main_company.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        sale = self.env['sale.order'].sudo(
            self.new_user.id).create({
                'partner_id': self.partner.id,
                'order_line': [
                    (0, 0, {
                        'product_id': self.product_01.id,
                        'price_unit': self.product_01.list_price,
                        'product_uom_qty': 50,
                    }),
                    (0, 0, {
                        'product_id': self.product_02.id,
                        'price_unit': self.product_02.list_price,
                        'product_uom_qty': 1,
                    }),
                ]
            })
        self.assertEqual(len(sale.order_line), 4)
        line_product_01 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_01)
        self.assertEqual(line_product_01.product_uom_qty, 50)
        self.assertEqual(line_product_01.price_unit, 100)
        self.assertEqual(line_product_01.price_subtotal, 5000)
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
        self.assertEqual(line_product_maintenance.price_unit, 500)
        self.assertEqual(line_product_maintenance.price_subtotal, 500)
        self.assertTrue(
            line_product_maintenance.is_not_increases_maintenance_price)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t50.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)

    def test_sale_order_line_maintenance_change_check_qtys_price_and_discount(
            self):
        self.main_company.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        sale = self.env['sale.order'].sudo(
            self.new_user.id).create({
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
        self.assertEqual(len(sale.order_line), 4)
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
        self.assertTrue(
            line_product_maintenance.is_not_increases_maintenance_price)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t1.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)
        line_product_01.is_not_increases_maintenance_price = True
        self.assertEqual(line_product_01.product_uom_qty, 1)
        self.assertEqual(line_product_01.price_unit, 100)
        self.assertEqual(line_product_01.price_subtotal, 100)
        line_product_02 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(line_product_02.product_uom_qty, 1)
        self.assertEqual(line_product_02.price_unit, 50)
        self.assertEqual(line_product_02.price_subtotal, 50)
        line_product_maintenance = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(line_product_maintenance.product_uom_qty, 1)
        self.assertEqual(line_product_maintenance.price_unit, 0)
        self.assertEqual(line_product_maintenance.price_subtotal, 0)
        self.assertNotIn(
            '\t1.0 Unit(s) x SERV1\n', line_product_maintenance.name)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n',
            line_product_maintenance.name)
        line_product_01.is_not_increases_maintenance_price = False
        line_product_maintenance = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(line_product_maintenance.product_uom_qty, 1)
        self.assertEqual(line_product_maintenance.price_unit, 115)
        self.assertEqual(line_product_maintenance.price_subtotal, 115)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t1.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)
        line_product_01.product_uom_qty = 2
        self.assertEqual(line_product_01.product_uom_qty, 2)
        self.assertEqual(line_product_01.price_unit, 100)
        self.assertEqual(line_product_01.price_subtotal, 200)
        line_product_maintenance = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(line_product_maintenance.product_uom_qty, 1)
        self.assertEqual(line_product_maintenance.price_unit, 115)
        self.assertEqual(line_product_maintenance.price_subtotal, 115)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t2.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)
        line_product_01.price_unit = 2000
        self.assertEqual(line_product_01.product_uom_qty, 2)
        self.assertEqual(line_product_01.price_unit, 2000)
        self.assertEqual(line_product_01.price_subtotal, 4000)
        line_product_maintenance = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(line_product_maintenance.product_uom_qty, 1)
        self.assertEqual(line_product_maintenance.price_unit, 400)
        self.assertEqual(line_product_maintenance.price_subtotal, 400)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t2.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)
        line_product_01.discount = 50
        self.assertEqual(line_product_01.product_uom_qty, 2)
        self.assertEqual(line_product_01.price_unit, 2000)
        self.assertEqual(line_product_01.price_subtotal, 2000)
        line_product_maintenance = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(line_product_maintenance.product_uom_qty, 1)
        self.assertEqual(line_product_maintenance.price_unit, 200)
        self.assertEqual(line_product_maintenance.price_subtotal, 200)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t2.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)

    def test_sale_order_line_maintenance_unlink_sale_line(self):
        self.main_company.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        sale = self.env['sale.order'].sudo(
            self.new_user.id).create({
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
        self.assertEqual(len(sale.order_line), 4)
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
        self.assertTrue(
            line_product_maintenance.is_not_increases_maintenance_price)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t1.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)
        line_product_01.unlink()
        self.assertEqual(len(sale.order_line), 3)
        line_product_01 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_01)
        self.assertFalse(line_product_01)
        line_product_02 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(line_product_02.product_uom_qty, 1)
        self.assertEqual(line_product_02.price_unit, 50)
        self.assertEqual(line_product_02.price_subtotal, 50)
        line_product_maintenance = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(line_product_maintenance.product_uom_qty, 1)
        self.assertEqual(line_product_maintenance.price_unit, 0)
        self.assertEqual(line_product_maintenance.price_subtotal, 0)
        self.assertNotIn(
            '\t1.0 Unit(s) x SERV1\n', line_product_maintenance.name)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n',
            line_product_maintenance.name)

    def test_sale_order_line_maintenance_not_modify_maintenance_line(self):
        self.main_company.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        sale = self.env['sale.order'].sudo(
            self.new_user.id).create({
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
        self.assertEqual(len(sale.order_line), 4)
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
        self.assertTrue(
            line_product_maintenance.is_not_increases_maintenance_price)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t1.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)
        with self.assertRaises(exceptions.UserError) as result:
            line_product_maintenance.price_unit = 999
        self.assertIn(
            'It is not allowed to modify a maintenance line.',
            result.exception.name)

    def test_sale_order_line_is_maintenance_line_unique(self):
        self.main_company.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        sale = self.env['sale.order'].sudo(
            self.new_user.id).create({
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
        self.assertEqual(len(sale.order_line), 4)
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
        self.assertTrue(
            line_product_maintenance.is_not_increases_maintenance_price)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t1.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['sale.order.line'].create({
                'order_id': sale.id,
                'is_maintenance_line': True,
                'product_id': self.product_maintenance.id,
                'product_uom_qty': 1,
            })
        self.assertIn(
            'Only one maintenance line can exist on a sales order.',
            result.exception.name)

    def test_sale_order_line_multicompany_difference_product_for_company(self):
        self.new_user.write({
            'company_ids': [(4, self.company_2.id)],
            'company_id': self.company_2.id,
        })
        product_tmpl_maintenance_2 = self.env['product.template'].sudo(
            self.new_user.id).create({
                'type': 'service',
                'company_id': False,
                'name': 'Maintenance product 2',
                'default_code': 'MAINTENANCE2',
                'standard_price': 1,
                'list_price': 88,
            })
        product_maintenance2 = product_tmpl_maintenance_2.product_variant_id
        self.company_2.maintenance_product_tmpl_id = (
            product_tmpl_maintenance_2.id)
        sale = self.env['sale.order'].sudo(
            self.new_user.id).create({
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
        self.assertEqual(len(sale.order_line), 4)
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
        line_product_maintenance2 = sale.order_line.filtered(
            lambda ln: ln.product_id == product_maintenance2)
        self.assertEqual(line_product_maintenance2.product_uom_qty, 1)
        self.assertEqual(line_product_maintenance2.price_unit, 88)
        self.assertEqual(line_product_maintenance2.price_subtotal, 88)
        self.assertTrue(
            line_product_maintenance2.is_not_increases_maintenance_price)
        self.assertEqual(
            '[MAINTENANCE2] Maintenance product 2\n\t1.0 Unit(s) x SERV1\n',
            line_product_maintenance2.name)

    def test_sale_order_line_multicompany_same_product_for_companies(self):
        self.assertEquals(self.new_user.company_id, self.main_company)
        self.assertFalse(self.product_tmpl_maintenance.company_id)
        self.main_company.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        self.company_2.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        self.assertEquals(
            self.main_company.maintenance_product_tmpl_id,
            self.product_tmpl_maintenance)
        self.assertEquals(
            self.company_2.maintenance_product_tmpl_id,
            self.product_tmpl_maintenance)
        sale_company_1 = self.env['sale.order'].sudo(
            self.new_user.id).create({
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
        self.assertEqual(sale_company_1.company_id, self.main_company)
        self.assertEqual(len(sale_company_1.order_line), 4)
        line_product_01 = sale_company_1.order_line.filtered(
            lambda ln: ln.product_id == self.product_01)
        self.assertEqual(line_product_01.product_uom_qty, 1)
        self.assertEqual(line_product_01.price_unit, 100)
        self.assertEqual(line_product_01.price_subtotal, 100)
        self.assertFalse(line_product_01.is_not_increases_maintenance_price)
        line_product_02 = sale_company_1.order_line.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(line_product_02.product_uom_qty, 1)
        self.assertEqual(line_product_02.price_unit, 50)
        self.assertEqual(line_product_02.price_subtotal, 50)
        self.assertTrue(line_product_02.is_not_increases_maintenance_price)
        line_product_maintenance = sale_company_1.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(line_product_maintenance.product_uom_qty, 1)
        self.assertEqual(line_product_maintenance.price_unit, 115)
        self.assertEqual(line_product_maintenance.price_subtotal, 115)
        self.assertTrue(
            line_product_maintenance.is_not_increases_maintenance_price)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t1.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)
        self.new_user.write({
            'company_ids': [(4, self.company_2.id)],
            'company_id': self.company_2.id,
        })
        self.assertEquals(self.new_user.company_id, self.company_2)
        sale_company_2 = self.env['sale.order'].sudo(
            self.new_user.id).create({
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
        self.assertEqual(sale_company_2.company_id, self.company_2)
        self.assertEqual(len(sale_company_2.order_line), 4)
        line_product_01 = sale_company_2.order_line.filtered(
            lambda ln: ln.product_id == self.product_01)
        self.assertEqual(line_product_01.product_uom_qty, 1)
        self.assertEqual(line_product_01.price_unit, 100)
        self.assertEqual(line_product_01.price_subtotal, 100)
        self.assertFalse(line_product_01.is_not_increases_maintenance_price)
        line_product_02 = sale_company_2.order_line.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(line_product_02.product_uom_qty, 1)
        self.assertEqual(line_product_02.price_unit, 50)
        self.assertEqual(line_product_02.price_subtotal, 50)
        self.assertTrue(line_product_02.is_not_increases_maintenance_price)
        line_product_maintenance = sale_company_2.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(line_product_maintenance.product_uom_qty, 1)
        self.assertEqual(line_product_maintenance.price_unit, 115)
        self.assertEqual(line_product_maintenance.price_subtotal, 115)
        self.assertTrue(
            line_product_maintenance.is_not_increases_maintenance_price)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t1.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)

    def test_sale_order_line_maintainance_line_price_zero(self):
        self.main_company.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        sale = self.env['sale.order'].sudo(
            self.new_user.id).create({
                'partner_id': self.partner.id,
                'order_line': [
                    (0, 0, {
                        'product_id': self.product_02.id,
                        'price_unit': self.product_02.list_price,
                        'product_uom_qty': 1,
                    }),
                ]
            })
        self.assertEqual(len(sale.order_line), 3)
        line_product_02 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(line_product_02.product_uom_qty, 1)
        self.assertEqual(line_product_02.price_unit, 50)
        self.assertEqual(line_product_02.price_subtotal, 50)
        self.assertTrue(line_product_02.is_not_increases_maintenance_price)
        line_product_maintenance = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(line_product_maintenance.product_uom_qty, 1)
        self.assertEqual(line_product_maintenance.price_unit, 0)
        self.assertEqual(line_product_maintenance.price_subtotal, 0)
        self.assertTrue(
            line_product_maintenance.is_not_increases_maintenance_price)
        self.assertNotIn(
            '\t1.0 Unit(s) x SERV1\n', line_product_maintenance.name)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n',
            line_product_maintenance.name)

    def test_sale_order_line_no_maintainance_line(self):
        self.assertFalse(self.main_company.maintenance_product_tmpl_id)
        sale = self.env['sale.order'].sudo(
            self.new_user.id).create({
                'partner_id': self.partner.id,
                'order_line': [
                    (0, 0, {
                        'product_id': self.product_02.id,
                        'price_unit': self.product_02.list_price,
                        'product_uom_qty': 1,
                    }),
                ]
            })
        self.assertEqual(len(sale.order_line), 1)
        line_product_02 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(line_product_02.product_uom_qty, 1)
        self.assertEqual(line_product_02.price_unit, 50)
        self.assertEqual(line_product_02.price_subtotal, 50)
        self.assertTrue(line_product_02.is_not_increases_maintenance_price)

    def test_sale_order_line_onchange_product_id(self):
        sale = self.env['sale.order'].sudo(
            self.new_user.id).create({
                'partner_id': self.partner.id,
            })
        line_obj = self.env['sale.order.line']
        line = line_obj.new({
            'order_id': sale.id,
            'product_id': self.product_01.id,
            'price_unit': self.product_01.list_price,
            'product_uom_qty': 1,
        })
        line.product_id_change()
        self.assertFalse(line.is_not_increases_maintenance_price)
        line = line_obj.new({
            'order_id': sale.id,
            'product_id': self.product_02.id,
            'price_unit': self.product_02.list_price,
            'product_uom_qty': 1,
        })
        line.product_id_change()
        self.assertTrue(line.is_not_increases_maintenance_price)

    def test_sale_order_line_unlink_maintenance_line(self):
        self.main_company.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        sale = self.env['sale.order'].sudo(
            self.new_user.id).create({
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
        self.assertEqual(len(sale.order_line), 4)
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
        self.assertTrue(
            line_product_maintenance.is_not_increases_maintenance_price)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t1.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)
        line_product_01.unlink()
        self.assertEqual(len(sale.order_line), 3)
        line_product_maintenance = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(line_product_maintenance.price_subtotal, 0)
        sale.sudo(self.new_user.id).write({
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEqual(len(sale.order_line), 4)
        line_product_maintenance = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(line_product_maintenance.price_subtotal, 115)
        line_product_maintenance.unlink()
        line_product_maintenance = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_maintenance)
        self.assertEqual(len(line_product_maintenance), 1)
        sale.order_line.unlink()
        self.assertEqual(len(sale.order_line), 0)

    def test_sale_order_line_unlink_all_sale(self):
        self.main_company.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        sale = self.env['sale.order'].sudo(
            self.new_user.id).create({
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
        self.assertEqual(len(sale.order_line), 4)
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
        self.assertTrue(
            line_product_maintenance.is_not_increases_maintenance_price)
        self.assertEqual(
            '[MAINTENANCE] Maintenance product\n\t1.0 Unit(s) x SERV1\n',
            line_product_maintenance.name)
        sale.unlink()
        sale = self.env['sale.order'].search([
            ('partner_id', '=', self.partner.id),
        ])
        self.assertFalse(sale)

    def test_copy_sale_order_with_maintenance_line(self):
        self.main_company.maintenance_product_tmpl_id = (
            self.product_tmpl_maintenance.id)
        original_sale = self.env['sale.order'].sudo(self.new_user.id).create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.assertEqual(len(original_sale.order_line), 3)
        copied_sale = original_sale.copy()
        self.assertEqual(
            len(copied_sale.order_line), len(original_sale.order_line))
        original_maintenance_line = original_sale.order_line.filtered(
            lambda ln: ln.is_maintenance_line)
        copied_maintenance_line = copied_sale.order_line.filtered(
            lambda ln: ln.is_maintenance_line)
        self.assertTrue(copied_maintenance_line)
        self.assertEqual(
            original_maintenance_line.product_id,
            copied_maintenance_line.product_id)
        self.assertEqual(
            original_maintenance_line.price_unit,
            copied_maintenance_line.price_unit)
        self.assertEqual(
            original_maintenance_line.product_uom_qty,
            copied_maintenance_line.product_uom_qty)
        self.assertEqual(copied_maintenance_line.price_unit, 115)
        self.assertEqual(copied_maintenance_line.product_uom_qty, 1)
        self.assertTrue(
            copied_maintenance_line.is_not_increases_maintenance_price)
        self.assertEqual(
            copied_maintenance_line.name,
            '[MAINTENANCE] Maintenance product\n\t1.0 Unit(s) x SERV1\n')
