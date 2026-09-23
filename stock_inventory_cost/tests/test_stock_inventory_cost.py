# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests.common import TransactionCase


class TestInventoryCost(TransactionCase):

    def setUp(self):
        super(TestInventoryCost, self).setUp()
        self.company = self.env.ref('base.main_company')
        self.warehouse = self.env.ref('stock.warehouse0')
        uom_m = self.env.ref('product.product_uom_meter')
        uom_cm = self.env.ref('product.product_uom_cm')
        self.product_1 = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.company.id,
            'name': 'Product 1',
            'standard_price': 80,
            'list_price': 100,
            'uom_id': uom_m.id,
            'uom_po_id': uom_m.id,
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product 2',
            'standard_price': 30,
            'list_price': 40,
            'uom_id': uom_m.id,
            'uom_po_id': uom_m.id,
        })
        self.product_3 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product 3',
            'standard_price': 50,
            'list_price': 70,
            'uom_id': uom_cm.id,
            'uom_po_id': uom_m.id,
        })
        self.user_1 = self.create_user('1', self.company.id, [self.company.id])

    def create_user(self, user_name, company_id, company_ids):
        partner = self.env['res.partner'].create({
            'name': 'User %s' % user_name,
            'email': 'user_%s@test.com' % user_name,
        })
        return self.env['res.users'].create({
            'partner_id': partner.id,
            'company_id': company_id,
            'company_ids': [(6, 0, company_ids)],
            'name': 'User %s' % user_name,
            'login': 'user_%s' % user_name,
            'password': 'user_%s' % user_name,
            'groups_id': [(6, 0, [
                self.ref('base.group_user'),
                self.ref('stock.group_stock_manager'),
            ])],
        })

    def get_real_stock(self, user, product, location):
        qty_product_dict = product.sudo(user.id).with_context(
            location=location.id)._product_available()
        return qty_product_dict[product.id]['qty_available']

    def create_inventory(self, user, name, location, line_vals_list):
        inventory = self.env['stock.inventory'].sudo(user.id).create({
            'company_id': user.company_id.id,
            'name': '%s' % name,
            'location_id': location.id,
            'filter': 'partial',
        })
        inventory.prepare_inventory()
        default_vals = {
            'inventory_id': inventory.id,
            'location_id': location.id,
        }
        for line_val in line_vals_list:
            default_vals.update(line_val)
            self.env['stock.inventory.line'].sudo(user.id).create(default_vals)
        inventory.action_done()
        self.assertEquals(inventory.state, 'done')
        return inventory

    def test_inventory(self):
        location = self.warehouse.lot_stock_id
        line_vals = {
            'product_id': self.product_1.id,
            'product_uom_id': self.product_1.uom_id.id,
            'product_qty': 10,
        }
        inventory = self.create_inventory(
            self.user_1, 'Inv product_1 1', location, [line_vals])
        real_stock = self.get_real_stock(
            self.user_1, self.product_1, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock, 10)
        self.assertEquals(inventory.cost, 10 * 80)
        self.product_1.sudo(self.user_1.id).write({
            'standard_price': 90,
        })
        real_stock = self.get_real_stock(
            self.user_1, self.product_1, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock, 10)
        self.assertEquals(inventory.cost, 10 * 80)
        line_vals = {
            'product_id': self.product_1.id,
            'product_uom_id': self.product_1.uom_id.id,
            'product_qty': 7,
        }
        inventory = self.create_inventory(
            self.user_1, 'Inv product_1 2', location, [line_vals])
        real_stock = self.get_real_stock(
            self.user_1, self.product_1, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock, 7)
        self.assertEquals(inventory.cost, -3 * 90)

    def test_inventory_several_lines(self):
        location = self.warehouse.lot_stock_id
        line_vals_1 = {
            'product_id': self.product_1.id,
            'product_uom_id': self.product_1.uom_id.id,
            'product_qty': 10,
        }
        line_vals_2 = {
            'product_id': self.product_2.id,
            'product_uom_id': self.product_2.uom_id.id,
            'product_qty': 100,
        }
        inventory = self.create_inventory(
            self.user_1, 'Inv products 1, 2', location,
            [line_vals_1, line_vals_2])
        real_stock_p1 = self.get_real_stock(
            self.user_1, self.product_1, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_p1, 10)
        real_stock_p3 = self.get_real_stock(
            self.user_1, self.product_2, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_p3, 100)
        self.assertEquals(inventory.cost, 10 * 80 + 100 * 30)
        self.product_1.sudo(self.user_1.id).write({
            'standard_price': 99,
        })
        real_stock_p1 = self.get_real_stock(
            self.user_1, self.product_1, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_p1, 10)
        real_stock_p3 = self.get_real_stock(
            self.user_1, self.product_2, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_p3, 100)
        self.assertEquals(inventory.cost, 10 * 80 + 100 * 30)
        line_vals_1 = {
            'product_id': self.product_1.id,
            'product_uom_id': self.product_1.uom_id.id,
            'product_qty': 7,
        }
        line_vals_2 = {
            'product_id': self.product_2.id,
            'product_uom_id': self.product_2.uom_id.id,
            'product_qty': 33,
        }
        inventory = self.create_inventory(
            self.user_1, 'Inv products 1, 2', location,
            [line_vals_1, line_vals_2])
        real_stock_p1 = self.get_real_stock(
            self.user_1, self.product_1, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_p1, 7)
        real_stock_p3 = self.get_real_stock(
            self.user_1, self.product_2, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_p3, 33)
        self.assertEquals(inventory.cost, -(10 - 7) * 99 - (100 - 33) * 30)

    def test_inventory_several_lines_different_locations_moves(self):
        location = self.warehouse.lot_stock_id
        line_vals_1 = {
            'product_id': self.product_1.id,
            'product_uom_id': self.product_1.uom_id.id,
            'product_qty': 10,
        }
        line_vals_2 = {
            'product_id': self.product_2.id,
            'product_uom_id': self.product_1.uom_id.id,
            'product_qty': 100,
        }
        inventory = self.create_inventory(
            self.user_1, 'Inv products 1, 2', location,
            [line_vals_1, line_vals_2])
        real_stock_p1 = self.get_real_stock(
            self.user_1, self.product_1, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_p1, 10)
        real_stock_p3 = self.get_real_stock(
            self.user_1, self.product_2, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_p3, 100)
        self.assertEquals(inventory.cost, 10 * 80 + 100 * 30)
        self.product_1.sudo(self.user_1.id).write({
            'standard_price': 99,
        })
        real_stock_p1 = self.get_real_stock(
            self.user_1, self.product_1, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_p1, 10)
        real_stock_p3 = self.get_real_stock(
            self.user_1, self.product_2, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_p3, 100)
        self.assertEquals(inventory.cost, 10 * 80 + 100 * 30)
        line_vals_1 = {
            'product_id': self.product_1.id,
            'product_uom_id': self.product_1.uom_id.id,
            'product_qty': 7,
        }
        line_vals_2 = {
            'product_id': self.product_2.id,
            'product_uom_id': self.product_2.uom_id.id,
            'product_qty': 150,
        }
        inventory = self.create_inventory(
            self.user_1, 'Inv products 1, 2', location,
            [line_vals_1, line_vals_2])
        real_stock_p1 = self.get_real_stock(
            self.user_1, self.product_1, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_p1, 7)
        real_stock_p3 = self.get_real_stock(
            self.user_1, self.product_2, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_p3, 150)
        self.assertEquals(inventory.cost, -(10 - 7) * 99 - (100 - 150) * 30)

    def test_inventory_convert_uom_po(self):
        location = self.warehouse.lot_stock_id
        line_vals = {
            'product_id': self.product_3.id,
            'product_uom_id': self.product_3.uom_id.id,
            'product_qty': 5000,
        }
        inventory = self.create_inventory(
            self.user_1, 'Inv product_3 1', location, [line_vals])
        real_stock = self.get_real_stock(
            self.user_1, self.product_3, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock, 5000)
        self.assertEquals(inventory.cost, 5000 / 100 * 50)

        self.product_3.sudo(self.user_1.id).write({
            'standard_price': 90,
        })
        real_stock = self.get_real_stock(
            self.user_1, self.product_3, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock, 5000)
        self.assertEquals(inventory.cost, 5000 / 100 * 50)
        line_vals = {
            'product_id': self.product_3.id,
            'product_uom_id': self.product_3.uom_id.id,
            'product_qty': 7,
        }
        inventory = self.create_inventory(
            self.user_1, 'Inv product_3 2', location, [line_vals])
        real_stock = self.get_real_stock(
            self.user_1, self.product_3, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock, 7)
        qty_convert = 4993. / 100
        self.assertEquals(inventory.cost, - qty_convert * 90)
