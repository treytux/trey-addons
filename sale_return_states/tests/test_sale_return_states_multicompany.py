###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleReturnStatesMulticompany(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].create({
            'name': 'Company test 2',
            'email': 'test@test2.com',
        })
        self.pricelist = self.env['product.pricelist'].create({
            'company_id': self.company.id,
            'name': 'Company pricelist 2',
        })
        self.stock_wh = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company.id),
        ], limit=1, order='id asc')
        self.stock_location = self.stock_wh.lot_stock_id
        self.customer_location = self.env.ref(
            'stock.stock_location_customers')
        self.return_location = self.env['stock.location'].create({
            'company_id': self.company.id,
            'name': 'Return location 2',
            'usage': 'return',
        })
        self.scrap_location = self.env.ref('stock.stock_location_scrapped')
        self.customer_company = self.env['res.partner'].create({
            'name': 'Test customer',
            'customer': True,
            'email': 'test@test2.com'
        })
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'company_ids': [(6, 0, [self.company.id])],
            'company_id': self.company.id,
            'groups_id': [
                (4, self.env.ref('sales_team.group_sale_manager').id),
                (4, self.env.ref('stock.group_stock_manager').id),
                (4, self.env.ref('base.group_user').id),
            ],
        })
        self.user.partner_id.write({
            'email': 'partnermail@test.com',
        })
        self.product_1 = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.company.id,
            'name': 'Test product 1',
            'standard_price': 15,
            'list_price': 15,
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.company.id,
            'name': 'Test product 2',
            'standard_price': 20,
            'list_price': 20,
        })
        self.product_3 = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.company.id,
            'name': 'Test product 3',
            'standard_price': 25,
            'list_price': 25,
        })
        self.product_4 = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.company.id,
            'name': 'Test product 4',
            'standard_price': 30,
            'list_price': 30,
        })

    def picking_transfer(self, picking):
        picking.sudo(user=self.user).action_confirm()
        picking.sudo(user=self.user).action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.sudo(user=self.user).action_done()

    def update_qty_on_hand(self, product, location, new_qty):
        wizard_model = self.env['stock.change.product.qty']
        wizard = wizard_model.sudo(user=self.user).create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.sudo(user=self.user).change_product_qty()
        self.assertEquals(product.with_context(
            location=location.id).qty_available, new_qty)

    def test_sale_return_change_multicompany(self):
        self.update_qty_on_hand(
            self.product_1, self.stock_location, 100)
        self.assertEquals(self.product_1.with_context(
            location=self.stock_location.id).qty_available, 100)
        sale_return = self.env['sale.order'].sudo(user=self.user).create({
            'name': 'test sale return',
            'partner_id': self.customer_company.id,
            'warehouse_id': self.stock_wh.id,
            'pricelist_id': self.pricelist.id,
            'is_return': True,
        })
        sale_return.sudo(user=self.user).onchange_partner_id()
        vline = self.env['sale.order.line'].sudo(user=self.user).new({
            'order_id': sale_return.id,
            'ttype': 'change',
            'name': self.product_1.name,
            'product_id': self.product_1.id,
            'product_uom_qty': 10,
            'product_uom': self.product_1.uom_id.id,
            'price_unit': self.product_1.list_price,
        })
        vline.sudo(user=self.user).product_id_change()
        self.env['sale.order.line'].sudo(user=self.user).create(
            vline._convert_to_write(vline._cache))
        self.assertTrue(sale_return)
        sale_return.sudo(user=self.user).action_confirm()
        self.assertEquals(sale_return.state, 'sale')
        self.assertEquals(len(sale_return.picking_ids), 3)
        self.assertEquals(len(sale_return.order_line), 1)
        picking1 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.customer_location
            and p.location_dest_id == self.return_location)
        self.assertTrue(picking1)
        self.assertEquals(picking1.state, 'assigned')
        self.assertEquals(picking1.picking_type_id, self.stock_wh.in_type_id)
        picking2 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.scrap_location)
        self.assertTrue(picking2)
        self.assertEquals(picking2.state, 'waiting')
        self.assertEquals(picking2.picking_type_id, self.stock_wh.int_type_id)
        picking3 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.stock_location
            and p.location_dest_id == self.customer_location)
        self.assertTrue(picking3)
        self.assertEquals(picking3.state, 'confirmed')
        self.assertEquals(picking3.picking_type_id, self.stock_wh.out_type_id)
        self.picking_transfer(picking1)
        self.assertEquals(picking1.state, 'done')
        self.assertEquals(picking2.state, 'assigned')
        self.assertEquals(picking3.state, 'confirmed')
        self.picking_transfer(picking2)
        self.assertEquals(picking2.state, 'done')
        self.assertEquals(picking3.state, 'confirmed')
        self.picking_transfer(picking3)
        self.assertEquals(picking3.state, 'done')
        self.assertEquals(self.product_1.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product_1.with_context(
            location=self.stock_location.id).qty_available, 90)
        self.assertEquals(self.product_1.with_context(
            location=self.scrap_location.id).qty_available, 10)
        self.assertEquals(self.product_1.with_context(
            location=self.customer_location.id).qty_available, 0)

    def test_sale_return_repentance_multicompany(self):
        self.update_qty_on_hand(
            self.product_1, self.stock_location, 100)
        self.assertEquals(self.product_1.with_context(
            location=self.stock_location.id).qty_available, 100)
        sale_return = self.env['sale.order'].sudo(user=self.user).create({
            'name': 'test sale return',
            'partner_id': self.customer_company.id,
            'warehouse_id': self.stock_wh.id,
            'pricelist_id': self.pricelist.id,
            'is_return': True,
        })
        sale_return.sudo(user=self.user).onchange_partner_id()
        vline = self.env['sale.order.line'].sudo(user=self.user).new({
            'order_id': sale_return.id,
            'ttype': 'repentance',
            'name': self.product_1.name,
            'product_id': self.product_1.id,
            'product_uom_qty': 10,
            'product_uom': self.product_1.uom_id.id,
            'price_unit': self.product_1.list_price,
        })
        vline.sudo(user=self.user).product_id_change()
        self.env['sale.order.line'].sudo(user=self.user).create(
            vline._convert_to_write(vline._cache))
        self.assertTrue(sale_return)
        sale_return.sudo(user=self.user).action_confirm()
        self.assertEquals(sale_return.state, 'sale')
        self.assertEquals(len(sale_return.picking_ids), 2)
        self.assertEquals(len(sale_return.order_line), 1)
        picking1 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.customer_location
            and p.location_dest_id == self.return_location)
        self.assertTrue(picking1)
        self.assertEquals(picking1.state, 'assigned')
        self.assertEquals(picking1.picking_type_id, self.stock_wh.in_type_id)
        picking2 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.stock_location)
        self.assertTrue(picking2)
        self.assertEquals(picking2.state, 'waiting')
        self.assertEquals(picking2.picking_type_id, self.stock_wh.int_type_id)
        self.picking_transfer(picking1)
        self.assertEquals(picking1.state, 'done')
        self.assertEquals(picking2.state, 'assigned')
        self.picking_transfer(picking2)
        self.assertEquals(picking2.state, 'done')
        self.assertEquals(self.product_1.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product_1.with_context(
            location=self.stock_location.id).qty_available, 110)
        self.assertEquals(self.product_1.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product_1.with_context(
            location=self.customer_location.id).qty_available, -10)

    def test_sale_return_change_no_stock_multicompany(self):
        self.update_qty_on_hand(
            self.product_1, self.stock_location, 100)
        self.assertEquals(self.product_1.with_context(
            location=self.stock_location.id).qty_available, 100)
        sale_return = self.env['sale.order'].sudo(user=self.user).create({
            'name': 'test sale return',
            'partner_id': self.customer_company.id,
            'warehouse_id': self.stock_wh.id,
            'pricelist_id': self.pricelist.id,
            'is_return': True,
        })
        sale_return.sudo(user=self.user).onchange_partner_id()
        vline = self.env['sale.order.line'].sudo(user=self.user).new({
            'order_id': sale_return.id,
            'ttype': 'no_stock',
            'name': self.product_1.name,
            'product_id': self.product_1.id,
            'product_uom_qty': 10,
            'product_uom': self.product_1.uom_id.id,
            'price_unit': self.product_1.list_price,
        })
        vline.sudo(user=self.user).product_id_change()
        self.env['sale.order.line'].sudo(user=self.user).create(
            vline._convert_to_write(vline._cache))
        self.assertTrue(sale_return)
        sale_return.sudo(user=self.user).action_confirm()
        self.assertEquals(sale_return.state, 'sale')
        self.assertEquals(len(sale_return.picking_ids), 2)
        self.assertEquals(len(sale_return.order_line), 1)
        picking1 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.customer_location
            and p.location_dest_id == self.return_location)
        self.assertTrue(picking1)
        self.assertEquals(picking1.state, 'assigned')
        self.assertEquals(picking1.picking_type_id, self.stock_wh.in_type_id)
        picking2 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.scrap_location)
        self.assertTrue(picking2)
        self.assertEquals(picking2.state, 'waiting')
        self.assertEquals(picking2.picking_type_id, self.stock_wh.int_type_id)
        self.picking_transfer(picking1)
        self.assertEquals(picking1.state, 'done')
        self.assertEquals(picking2.state, 'assigned')
        self.picking_transfer(picking2)
        self.assertEquals(picking2.state, 'done')
        self.assertEquals(self.product_1.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product_1.with_context(
            location=self.stock_location.id).qty_available, 100)
        self.assertEquals(self.product_1.with_context(
            location=self.scrap_location.id).qty_available, 10)
        self.assertEquals(self.product_1.with_context(
            location=self.customer_location.id).qty_available, -10)

    def test_sale_return_repaired_no_default_multicompany(self):
        self.update_qty_on_hand(
            self.product_1, self.stock_location, 100)
        self.assertEquals(self.product_1.with_context(
            location=self.stock_location.id).qty_available, 100)
        sale_return = self.env['sale.order'].sudo(user=self.user).create({
            'name': 'test sale return',
            'partner_id': self.customer_company.id,
            'warehouse_id': self.stock_wh.id,
            'pricelist_id': self.pricelist.id,
            'is_return': True,
        })
        sale_return.sudo(user=self.user).onchange_partner_id()
        vline = self.env['sale.order.line'].sudo(user=self.user).new({
            'order_id': sale_return.id,
            'ttype': 'repaired',
            'name': self.product_1.name,
            'product_id': self.product_1.id,
            'product_uom_qty': 10,
            'product_uom': self.product_1.uom_id.id,
            'price_unit': self.product_1.list_price,
        })
        vline.sudo(user=self.user).product_id_change()
        self.env['sale.order.line'].sudo(user=self.user).create(
            vline._convert_to_write(vline._cache))
        self.assertTrue(sale_return)
        sale_return.sudo(user=self.user).action_confirm()
        self.assertEquals(sale_return.state, 'sale')
        self.assertEquals(len(sale_return.picking_ids), 2)
        self.assertEquals(len(sale_return.order_line), 1)
        picking1 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.customer_location
            and p.location_dest_id == self.return_location)
        self.assertTrue(picking1)
        self.assertEquals(picking1.state, 'assigned')
        self.assertEquals(picking1.picking_type_id, self.stock_wh.in_type_id)
        picking2 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.customer_location)
        self.assertTrue(picking2)
        self.assertEquals(picking2.state, 'waiting')
        self.assertEquals(picking2.picking_type_id, self.stock_wh.out_type_id)
        self.picking_transfer(picking1)
        self.assertEquals(picking1.state, 'done')
        self.assertEquals(picking2.state, 'assigned')
        self.picking_transfer(picking2)
        self.assertEquals(picking2.state, 'done')
        self.assertEquals(self.product_1.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product_1.with_context(
            location=self.stock_location.id).qty_available, 100)
        self.assertEquals(self.product_1.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product_1.with_context(
            location=self.customer_location.id).qty_available, 0)

    def test_sale_return_multiple_tipology_multicompany(self):
        self.update_qty_on_hand(
            self.product_1, self.stock_location, 100)
        self.assertEquals(self.product_1.with_context(
            location=self.stock_location.id).qty_available, 100)
        sale_return = self.env['sale.order'].sudo(user=self.user).create({
            'name': 'test sale return',
            'partner_id': self.customer_company.id,
            'warehouse_id': self.stock_wh.id,
            'pricelist_id': self.pricelist.id,
            'is_return': True,
            'order_line': [
                (0, 0, {
                    'name': self.product_1.name,
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1,
                    'ttype': 'change'}),
                (0, 0, {
                    'name': self.product_2.name,
                    'product_id': self.product_2.id,
                    'product_uom_qty': 2,
                    'ttype': 'repentance'}),
                (0, 0, {
                    'name': self.product_3.name,
                    'product_id': self.product_3.id,
                    'product_uom_qty': 3,
                    'ttype': 'repaired'}),
                (0, 0, {
                    'name': self.product_4.name,
                    'product_id': self.product_4.id,
                    'product_uom_qty': 4,
                    'ttype': 'out_warranty'}),
            ]
        })
        self.assertTrue(sale_return)
        sale_return.sudo(user=self.user).action_confirm()
        self.assertEquals(sale_return.state, 'sale')
        self.assertEquals(len(sale_return.picking_ids), 6)
        self.assertEquals(len(sale_return.order_line), 4)
        picking_return = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.customer_location
            and p.location_dest_id == self.return_location)
        self.assertTrue(picking_return)
        self.assertEquals(picking_return.state, 'assigned')
        self.assertEquals(
            picking_return.picking_type_id, self.stock_wh.in_type_id)
        picking_repaired_to_customer = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.customer_location
            and p.move_lines.product_id.name == 'Test product 3')
        self.assertTrue(picking_repaired_to_customer)
        self.assertEquals(picking_repaired_to_customer.state, 'waiting')
        self.assertEquals(
            picking_repaired_to_customer.picking_type_id,
            self.stock_wh.out_type_id)
        picking_to_stock = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.stock_location)
        self.assertTrue(picking_to_stock)
        self.assertEquals(picking_to_stock.state, 'waiting')
        self.assertEquals(
            picking_to_stock.picking_type_id, self.stock_wh.int_type_id)
        picking_out_warranty_to_customer = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.customer_location
            and p.move_lines.product_id.name == 'Test product 4')
        self.assertTrue(picking_out_warranty_to_customer)
        self.assertEquals(picking_out_warranty_to_customer.state, 'waiting')
        self.assertEquals(
            picking_out_warranty_to_customer.picking_type_id,
            self.stock_wh.out_type_id)
        picking_stock_to_customer = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.stock_location
            and p.location_dest_id == self.customer_location)
        self.assertTrue(picking_stock_to_customer)
        self.assertEquals(picking_stock_to_customer.state, 'confirmed')
        self.assertEquals(
            picking_stock_to_customer.picking_type_id,
            self.stock_wh.out_type_id)
        picking_to_scrap = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.scrap_location)
        self.assertTrue(picking_stock_to_customer)
        self.assertEquals(picking_to_scrap.state, 'waiting')
        self.assertEquals(
            picking_to_scrap.picking_type_id, self.stock_wh.int_type_id)
        self.picking_transfer(picking_return)
        self.assertEquals(picking_return.state, 'done')
        self.assertEquals(picking_repaired_to_customer.state, 'assigned')
        self.picking_transfer(picking_repaired_to_customer)
        self.assertEquals(picking_repaired_to_customer.state, 'done')
        self.assertEquals(picking_to_stock.state, 'assigned')
        self.picking_transfer(picking_to_stock)
        self.assertEquals(picking_to_stock.state, 'done')
        self.assertEquals(picking_out_warranty_to_customer.state, 'assigned')
        self.picking_transfer(picking_out_warranty_to_customer)
        self.assertEquals(picking_out_warranty_to_customer.state, 'done')
        self.assertEquals(picking_stock_to_customer.state, 'confirmed')
        self.picking_transfer(picking_stock_to_customer)
        self.assertEquals(picking_stock_to_customer.state, 'done')
        self.assertEquals(picking_to_scrap.state, 'assigned')
        self.picking_transfer(picking_to_scrap)
        self.assertEquals(picking_to_scrap.state, 'done')
        self.assertEquals(self.product_1.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product_1.with_context(
            location=self.stock_location.id).qty_available, 99)
        self.assertEquals(self.product_1.with_context(
            location=self.scrap_location.id).qty_available, 1)
        self.assertEquals(self.product_1.with_context(
            location=self.customer_location.id).qty_available, 0)
        self.assertEquals(self.product_2.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product_2.with_context(
            location=self.stock_location.id).qty_available, 2)
        self.assertEquals(self.product_2.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product_2.with_context(
            location=self.customer_location.id).qty_available, -2)
        self.assertEquals(self.product_3.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product_3.with_context(
            location=self.stock_location.id).qty_available, 0)
        self.assertEquals(self.product_3.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product_3.with_context(
            location=self.customer_location.id).qty_available, 0)
        self.assertEquals(self.product_4.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product_4.with_context(
            location=self.stock_location.id).qty_available, 0)
        self.assertEquals(self.product_4.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product_4.with_context(
            location=self.customer_location.id).qty_available, 0)
