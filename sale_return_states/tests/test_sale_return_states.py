###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleReturnStates(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.scrap_location = self.env.ref('stock.stock_location_scrapped')
        self.customer_location = self.env.ref('stock.stock_location_customers')
        self.stock_location = self.stock_wh.lot_stock_id
        self.return_location = self.env.ref(
            'sale_return_states.return_location')
        self.pricelist = self.env.ref('product.list0')
        self.in_picking_type = self.stock_wh.in_type_id
        self.internal_picking_type = self.stock_wh.int_type_id
        self.out_picking_type = self.stock_wh.out_type_id
        self.customer1 = self.env['res.partner'].create({
            'name': 'Test customer',
            'customer': True,
        })
        self.product1 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 10,
            'list_price': 15,
        })
        self.product2 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 2',
            'standard_price': 15,
            'list_price': 20,
        })
        self.product3 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 3',
            'standard_price': 20,
            'list_price': 25,
        })
        self.product4 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 4',
            'standard_price': 25,
            'list_price': 30,
        })

    def create_sale_order(
            self, partner, warehouse, pricelist, product, qty, is_return,
            ttype):
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'warehouse_id': warehouse.id,
            'pricelist_id': pricelist.id,
            'is_return': is_return,
        })
        order.onchange_partner_id()
        vline = self.env['sale.order.line'].new({
            'order_id': order.id,
            'ttype': ttype,
            'name': product.name,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'price_unit': product.list_price,
        })
        vline.product_id_change()
        self.env['sale.order.line'].create(
            vline._convert_to_write(vline._cache))
        return order

    def create_sale_order_multi(self, partner, warehouse):
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'warehouse_id': warehouse.id,
            'pricelist_id': self.pricelist.id,
            'is_return': True,
            'order_line': [
                (0, 0, {
                    'product_id': self.product1.id,
                    'product_uom_qty': 1,
                    'ttype': 'change'}),
                (0, 0, {
                    'product_id': self.product2.id,
                    'product_uom_qty': 2,
                    'ttype': 'repentance'}),
                (0, 0, {
                    'product_id': self.product3.id,
                    'product_uom_qty': 3,
                    'ttype': 'repaired'}),
                (0, 0, {
                    'product_id': self.product4.id,
                    'product_uom_qty': 4,
                    'ttype': 'out_warranty'}),
            ]
        })
        return order

    def picking_transfer(self, picking):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEquals(product.with_context(
            location=location.id).qty_available, new_qty)

    def test_sale_return_change(self):
        self.update_qty_on_hand(
            self.product1, self.stock_wh.lot_stock_id, 100)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        sale_return = self.create_sale_order(
            self.customer1, self.stock_wh, self.pricelist, self.product1, 10,
            True, 'change')
        self.assertTrue(sale_return)
        sale_return.action_confirm()
        self.assertEquals(sale_return.state, 'sale')
        self.assertEquals(len(sale_return.picking_ids), 3)
        self.assertEquals(len(sale_return.order_line), 1)
        picking1 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.customer_location
            and p.location_dest_id == self.return_location)
        self.assertTrue(picking1)
        self.assertEquals(picking1.state, 'assigned')
        self.assertEquals(picking1.picking_type_id, self.in_picking_type)
        picking2 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.scrap_location)
        self.assertTrue(picking2)
        self.assertEquals(picking2.state, 'waiting')
        self.assertEquals(picking2.picking_type_id, self.internal_picking_type)
        picking3 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.stock_location
            and p.location_dest_id == self.customer_location)
        self.assertTrue(picking3)
        self.assertEquals(picking3.state, 'confirmed')
        self.assertEquals(picking3.picking_type_id, self.out_picking_type)
        self.picking_transfer(picking1)
        self.assertEquals(picking1.state, 'done')
        self.assertEquals(picking2.state, 'assigned')
        self.assertEquals(picking3.state, 'confirmed')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location.id).qty_available, 100)
        self.assertEquals(self.product1.with_context(
            location=self.return_location.id).qty_available, 10)
        self.assertEquals(self.product1.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.customer_location.id).qty_available, -10)
        self.picking_transfer(picking2)
        self.assertEquals(picking2.state, 'done')
        self.assertEquals(picking3.state, 'confirmed')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location.id).qty_available, 100)
        self.assertEquals(self.product1.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.scrap_location.id).qty_available, 10)
        self.assertEquals(self.product1.with_context(
            location=self.customer_location.id).qty_available, -10)
        self.picking_transfer(picking3)
        self.assertEquals(picking3.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location.id).qty_available, 90)
        self.assertEquals(self.product1.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.scrap_location.id).qty_available, 10)
        self.assertEquals(self.product1.with_context(
            location=self.customer_location.id).qty_available, 0)

    def test_sale_return_repentance(self):
        sale_return = self.create_sale_order(
            self.customer1, self.stock_wh, self.pricelist, self.product1, 10,
            True, 'repentance')
        self.assertTrue(sale_return)
        sale_return.action_confirm()
        self.assertEquals(sale_return.state, 'sale')
        self.assertEquals(len(sale_return.picking_ids), 2)
        self.assertEquals(len(sale_return.order_line), 1)
        picking1 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.customer_location
            and p.location_dest_id == self.return_location)
        self.assertTrue(picking1)
        self.assertEquals(picking1.state, 'assigned')
        self.assertEquals(picking1.picking_type_id, self.in_picking_type)
        picking2 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.stock_location)
        self.assertTrue(picking2)
        self.assertEquals(picking2.state, 'waiting')
        self.assertEquals(
            picking2.picking_type_id, self.internal_picking_type)
        self.picking_transfer(picking1)
        self.assertEquals(picking1.state, 'done')
        self.assertEquals(picking2.state, 'assigned')
        self.assertEquals(self.product1.with_context(
            location=self.return_location.id).qty_available, 10)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.customer_location.id).qty_available, -10)
        self.picking_transfer(picking2)
        self.assertEquals(picking2.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location.id).qty_available, 10)
        self.assertEquals(self.product1.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.customer_location.id).qty_available, -10)

    def test_sale_return_change_no_stock(self):
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 0)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        sale_return = self.create_sale_order(
            self.customer1, self.stock_wh, self.pricelist, self.product1, 10,
            True, 'no_stock')
        self.assertTrue(sale_return)
        sale_return.action_confirm()
        self.assertEquals(sale_return.state, 'sale')
        self.assertEquals(len(sale_return.picking_ids), 2)
        self.assertEquals(len(sale_return.order_line), 1)
        picking1 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.customer_location
            and p.location_dest_id == self.return_location)
        self.assertTrue(picking1)
        self.assertEquals(picking1.state, 'assigned')
        self.assertEquals(picking1.picking_type_id, self.in_picking_type)
        picking2 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.scrap_location)
        self.assertTrue(picking2)
        self.assertEquals(picking2.state, 'waiting')
        self.assertEquals(picking2.picking_type_id, self.internal_picking_type)
        self.picking_transfer(picking1)
        self.assertEquals(picking1.state, 'done')
        self.assertEquals(picking2.state, 'assigned')
        self.assertEquals(self.product1.with_context(
            location=self.return_location.id).qty_available, 10)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.customer_location.id).qty_available, -10)
        self.picking_transfer(picking2)
        self.assertEquals(picking2.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.scrap_location.id).qty_available, 10)
        self.assertEquals(self.product1.with_context(
            location=self.customer_location.id).qty_available, -10)

    def test_sale_return_repaired_no_default(self):
        sale_return = self.create_sale_order(
            self.customer1, self.stock_wh, self.pricelist, self.product1, 10,
            True, 'repaired')
        self.assertTrue(sale_return)
        sale_return.action_confirm()
        self.assertEquals(sale_return.state, 'sale')
        self.assertEquals(len(sale_return.picking_ids), 2)
        self.assertEquals(len(sale_return.order_line), 1)
        picking1 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.customer_location
            and p.location_dest_id == self.return_location)
        self.assertTrue(picking1)
        self.assertEquals(picking1.state, 'assigned')
        self.assertEquals(picking1.picking_type_id, self.in_picking_type)
        picking2 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.customer_location)
        self.assertTrue(picking2)
        self.assertEquals(picking2.state, 'waiting')
        self.assertEquals(picking2.picking_type_id, self.out_picking_type)
        self.picking_transfer(picking1)
        self.assertEquals(picking1.state, 'done')
        self.assertEquals(picking2.state, 'assigned')
        self.assertEquals(self.product1.with_context(
            location=self.return_location.id).qty_available, 10)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.customer_location.id).qty_available, -10)
        self.picking_transfer(picking2)
        self.assertEquals(picking2.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.customer_location.id).qty_available, 0)

    def test_sale_return_out_warranty(self):
        sale_return = self.create_sale_order(
            self.customer1, self.stock_wh, self.pricelist, self.product1, 10,
            True, 'out_warranty')
        self.assertTrue(sale_return)
        sale_return.action_confirm()
        self.assertEquals(sale_return.state, 'sale')
        self.assertEquals(len(sale_return.picking_ids), 2)
        self.assertEquals(len(sale_return.order_line), 1)
        picking1 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.customer_location
            and p.location_dest_id == self.return_location)
        self.assertTrue(picking1)
        self.assertEquals(picking1.state, 'assigned')
        self.assertEquals(picking1.picking_type_id, self.in_picking_type)
        picking2 = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.customer_location)
        self.assertTrue(picking2)
        self.assertEquals(picking2.state, 'waiting')
        self.assertEquals(picking2.picking_type_id, self.out_picking_type)
        self.picking_transfer(picking1)
        self.assertEquals(picking1.state, 'done')
        self.assertEquals(picking2.state, 'assigned')
        self.assertEquals(self.product1.with_context(
            location=self.return_location.id).qty_available, 10)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.customer_location.id).qty_available, -10)
        self.picking_transfer(picking2)
        self.assertEquals(picking2.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.customer_location.id).qty_available, 0)

    def test_sale_return_multiple_tipology(self):
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        sale_return = self.create_sale_order_multi(
            self.customer1, self.stock_wh)
        self.assertTrue(sale_return)
        sale_return.action_confirm()
        self.assertEquals(sale_return.state, 'sale')
        self.assertEquals(len(sale_return.picking_ids), 6)
        self.assertEquals(len(sale_return.order_line), 4)
        picking_return = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.customer_location
            and p.location_dest_id == self.return_location)
        self.assertTrue(picking_return)
        self.assertEquals(picking_return.state, 'assigned')
        self.assertEquals(picking_return.picking_type_id, self.in_picking_type)
        picking_repaired_to_customer = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.customer_location
            and p.move_lines.product_id.name == 'Test product 3')
        self.assertTrue(picking_repaired_to_customer)
        self.assertEquals(picking_repaired_to_customer.state, 'waiting')
        self.assertEquals(
            picking_repaired_to_customer.picking_type_id,
            self.out_picking_type)
        picking_to_stock = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.stock_location)
        self.assertTrue(picking_to_stock)
        self.assertEquals(picking_to_stock.state, 'waiting')
        self.assertEquals(
            picking_to_stock.picking_type_id, self.internal_picking_type)
        picking_out_warranty_to_customer = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.customer_location
            and p.move_lines.product_id.name == 'Test product 4')
        self.assertTrue(picking_out_warranty_to_customer)
        self.assertEquals(picking_out_warranty_to_customer.state, 'waiting')
        self.assertEquals(
            picking_out_warranty_to_customer.picking_type_id,
            self.out_picking_type)
        picking_stock_to_customer = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.stock_location
            and p.location_dest_id == self.customer_location)
        self.assertTrue(picking_stock_to_customer)
        self.assertEquals(picking_stock_to_customer.state, 'confirmed')
        self.assertEquals(
            picking_stock_to_customer.picking_type_id, self.out_picking_type)
        picking_to_scrap = sale_return.picking_ids.filtered(
            lambda p: p.location_id == self.return_location
            and p.location_dest_id == self.scrap_location)
        self.assertTrue(picking_stock_to_customer)
        self.assertEquals(picking_to_scrap.state, 'waiting')
        self.assertEquals(
            picking_to_scrap.picking_type_id, self.internal_picking_type)
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
        self.assertEquals(self.product1.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location.id).qty_available, 99)
        self.assertEquals(self.product1.with_context(
            location=self.scrap_location.id).qty_available, 1)
        self.assertEquals(self.product1.with_context(
            location=self.customer_location.id).qty_available, 0)
        self.assertEquals(self.product2.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product2.with_context(
            location=self.stock_location.id).qty_available, 2)
        self.assertEquals(self.product2.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product2.with_context(
            location=self.customer_location.id).qty_available, -2)
        self.assertEquals(self.product3.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product3.with_context(
            location=self.stock_location.id).qty_available, 0)
        self.assertEquals(self.product3.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product3.with_context(
            location=self.customer_location.id).qty_available, 0)
        self.assertEquals(self.product4.with_context(
            location=self.return_location.id).qty_available, 0)
        self.assertEquals(self.product4.with_context(
            location=self.stock_location.id).qty_available, 0)
        self.assertEquals(self.product4.with_context(
            location=self.scrap_location.id).qty_available, 0)
        self.assertEquals(self.product4.with_context(
            location=self.customer_location.id).qty_available, 0)
