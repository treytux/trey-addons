###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestStockPickingReturnSupplier(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.customer = self.env['res.partner'].create({
            'name': 'Test customer',
            'customer': True,
            'company_id': self.company.id,
        })
        self.customer_loc = self.env.ref('stock.stock_location_customers')
        self.supplier_loc = self.env.ref('stock.stock_location_suppliers')
        self.supplier = self.env['res.partner'].create({
            'name': 'Test supplier',
            'supplier': True,
            'company_id': self.company.id,
        })
        self.category = self.env['res.partner.category'].create({
            'name': 'SP',
        })
        self.supplier.write({
            'category_id': [(6, 0, self.category.ids)],
        })
        self.warehouse = self.env.ref('stock.warehouse0')
        self.picking_type_dropshipping = self.env.ref(
            'stock_dropshipping.picking_type_dropship')
        self.dropshipping_route = self.env.ref(
            'stock_dropshipping.route_drop_shipping')
        self.product_dropshipping = self.env['product.product'].create({
            'name': 'Test product dropshipping',
            'type': 'product',
            'default_code': 'SP123456789',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.dropshipping_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 10,
            })],
        })
        self.picking_type = self.env['stock.picking.type'].browse(2)
        self.location_test = self.env['stock.location'].create({
            'name': 'Test location',
            'usage': 'internal',
        })

    def create_sale(self, product, quantity, warehouse, partner):
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'company_id': self.company.id,
            'warehouse_id': warehouse.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'price_unit': 10,
                'product_uom_qty': quantity,
            })]
        })
        sale.action_confirm()
        return sale

    def picking_transfer(self, picking, qty):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = qty
        picking.action_done()
        self.assertEquals(picking.state, 'done')

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEquals(product.with_context(
            location=location.id).qty_available, new_qty)

    def test_standard_mtd_purchase(self):
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(
            self.product_dropshipping, 1, self.warehouse, self.customer)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 0)
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line.product_uom_qty, 1)
        purchase.button_confirm()
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(len(purchase.picking_ids), 1)
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=1)
        self.assertEquals(
            purchase_picking.picking_type_id, self.picking_type_dropshipping)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(sale.picking_ids, purchase.picking_ids)
        self.assertEquals(
            sale.order_line[0].purchase_line_ids, purchase.order_line[0])
        self.assertEquals(sale.order_line[0].qty_delivered, 1)
        self.assertEquals(purchase_picking.state, 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=purchase_picking.ids,
            active_id=purchase_picking.ids[0],
        ).create({})
        return_picking.location_id = self.location_test.id
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        picking_ret = sale.picking_ids[0]
        self.picking_transfer(picking_ret, 1)
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(len(purchase.picking_ids), 2)
        wizard = self.env['stock.picking.return.supplier'].create({
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'picking_type': self.picking_type.id,
        })
        self.assertEquals(len(wizard.confirm_line_ids), 0)
        wizard.button_get_products_location()
        self.assertEquals(len(wizard.confirm_line_ids), 1)
        self.assertEquals(wizard.confirm_line_ids[0].wizard_id, wizard)
        self.assertEquals(
            wizard.confirm_line_ids[0].product_id, self.product_dropshipping)
        self.assertEquals(wizard.confirm_line_ids[0].picking_id, picking_ret)
        self.assertEquals(wizard.confirm_line_ids[0].qty, 1)
        self.assertEquals(
            wizard.confirm_line_ids[0].move_id, picking_ret.move_lines[0])
        self.assertEquals(wizard.qty_inventory, 1)
        self.assertEquals(wizard.qty_return, 1)
        res = wizard.button_accept()
        picking_supplier = self.env['stock.picking'].browse(res['res_id'])
        self.assertEquals(picking_supplier.partner_id, wizard.partner_id)
        self.assertEquals(
            picking_supplier.picking_type_id, wizard.picking_type)
        self.assertEquals(picking_supplier.location_id, wizard.location_id)
        self.assertEquals(
            picking_supplier.location_dest_id, self.supplier_loc)
        self.assertEquals(len(picking_supplier.move_lines), 1)
        self.assertEquals(
            picking_supplier.move_lines[0].name,
            self.product_dropshipping.name)
        self.assertEquals(
            picking_supplier.move_lines[0].picking_id, picking_supplier)
        self.assertEquals(
            picking_supplier.move_lines[0].product_id,
            self.product_dropshipping)
        self.assertEquals(
            picking_supplier.move_lines[0].product_uom,
            self.product_dropshipping.uom_id)
        self.assertEquals(picking_supplier.move_lines[0].product_uom_qty, 1)
        self.assertEquals(
            picking_supplier.move_lines[0].location_id, wizard.location_id)
        self.assertEquals(
            picking_supplier.move_lines[0].location_dest_id,
            self.supplier_loc)
        self.assertEquals(purchase.order_line[0].qty_received, 1)
        self.assertEquals(picking_supplier.picking_count, 1)
        self.assertEquals(picking_supplier.purchase_count, 1)
        res = picking_supplier.action_view_picking_purchase_link()
        self.assertEquals(res['domain'], [('id', 'in', purchase.ids)])
        self.assertEquals(res['res_id'], purchase.id)
        res = picking_supplier.action_view_picking_origin_move_link()
        self.assertEquals(res['domain'], [('id', 'in', picking_ret.ids)])
        self.assertEquals(res['res_id'], picking_ret.id)

    def test_standard_mtd_sale(self):
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(
            self.product_dropshipping, 1, self.warehouse, self.customer)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 0)
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line.product_uom_qty, 1)
        purchase.button_confirm()
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(len(purchase.picking_ids), 1)
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=1)
        self.assertEquals(
            purchase_picking.picking_type_id, self.picking_type_dropshipping)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking.location_dest_id, self.customer_loc)
        self.assertEquals(
            sale.order_line[0].purchase_line_ids, purchase.order_line[0])
        self.assertEquals(sale.order_line[0].qty_delivered, 1)
        self.assertEquals(purchase_picking.state, 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=purchase_picking.ids,
            active_id=purchase_picking.ids[0],
        ).create({})
        return_picking.location_id = self.location_test.id
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        picking_ret = sale.picking_ids[0]
        self.picking_transfer(picking_ret, 1)
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(len(purchase.picking_ids), 2)
        wizard = self.env['stock.picking.return.supplier'].create({
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'picking_type': self.picking_type.id,
        })
        wizard.button_get_products_location()
        self.assertEquals(len(wizard.confirm_line_ids), 1)
        self.assertEquals(wizard.confirm_line_ids[0].wizard_id, wizard)
        self.assertEquals(
            wizard.confirm_line_ids[0].picking_id, purchase.picking_ids[0])
        self.assertEquals(
            wizard.confirm_line_ids[0].product_id, self.product_dropshipping)
        self.assertEquals(wizard.confirm_line_ids[0].qty, 1)
        self.assertEquals(
            wizard.confirm_line_ids[0].move_id, picking_ret.move_lines[0])
        self.assertEquals(wizard.qty_inventory, 1)
        self.assertEquals(wizard.qty_inventory, 1)
        res = wizard.button_accept()
        picking_supplier = self.env['stock.picking'].browse(res['res_id'])
        self.assertEquals(picking_supplier.partner_id, wizard.partner_id)
        self.assertEquals(
            picking_supplier.picking_type_id, wizard.picking_type)
        self.assertEquals(picking_supplier.location_id, wizard.location_id)
        self.assertEquals(
            picking_supplier.location_dest_id, self.supplier_loc)
        self.assertEquals(len(picking_supplier.move_lines), 1)
        self.assertEquals(
            picking_supplier.move_lines[0].name,
            self.product_dropshipping.name)
        self.assertEquals(
            picking_supplier.move_lines[0].picking_id, picking_supplier)
        self.assertEquals(
            picking_supplier.move_lines[0].product_id,
            self.product_dropshipping)
        self.assertEquals(
            picking_supplier.move_lines[0].product_uom,
            self.product_dropshipping.uom_id)
        self.assertEquals(picking_supplier.move_lines[0].product_uom_qty, 1)
        self.assertEquals(
            picking_supplier.move_lines[0].location_id, wizard.location_id)
        self.assertEquals(
            picking_supplier.move_lines[0].location_dest_id,
            self.supplier_loc)
        self.assertEquals(purchase.order_line[0].qty_received, 1)
        self.assertEquals(picking_supplier.picking_count, 1)
        self.assertEquals(picking_supplier.purchase_count, 1)
        res = picking_supplier.action_view_picking_purchase_link()
        self.assertEquals(res['domain'], [('id', 'in', purchase.ids)])
        self.assertEquals(res['res_id'], purchase.id)
        res = picking_supplier.action_view_picking_origin_move_link()
        self.assertEquals(res['domain'], [('id', 'in', picking_ret.ids)])
        self.assertEquals(res['res_id'], picking_ret.id)

    def test_button_delete_all_lines(self):
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(
            self.product_dropshipping, 1, self.warehouse, self.customer)
        self.assertEquals(sale.state, 'sale')
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(len(purchase.order_line), 1)
        purchase.button_confirm()
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=1)
        self.assertEquals(sale.order_line[0].qty_delivered, 1)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=purchase_picking.ids,
            active_id=purchase_picking.ids[0],
        ).create({})
        return_picking.location_id = self.location_test.id
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        picking_ret = sale.picking_ids[0]
        self.picking_transfer(picking_ret, 1)
        wizard = self.env['stock.picking.return.supplier'].create({
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'picking_type': self.picking_type.id,
        })
        self.assertEquals(len(wizard.confirm_line_ids), 0)
        wizard.button_get_products_location()
        self.assertEquals(len(wizard.confirm_line_ids), 1)
        wizard.button_delete_lines()
        self.assertEquals(len(wizard.confirm_line_ids), 0)

    def test_return_supplier_check_purchase_orders(self):
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(
            self.product_dropshipping, 1, self.warehouse, self.customer)
        self.assertEquals(sale.state, 'sale')
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(len(purchase.order_line), 1)
        purchase.button_confirm()
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=1)
        self.assertEquals(sale.order_line[0].qty_delivered, 1)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=purchase_picking.ids,
            active_id=purchase_picking.ids[0],
        ).create({})
        return_picking.location_id = self.location_test.id
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        picking_ret = sale.picking_ids[0]
        self.picking_transfer(picking_ret, 1)
        wizard = self.env['stock.picking.return.supplier'].create({
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'picking_type': self.picking_type.id,
        })
        self.assertEquals(len(wizard.confirm_line_ids), 0)
        wizard.button_get_products_location()
        self.assertEquals(len(wizard.confirm_line_ids), 1)
        line = wizard.confirm_line_ids[0]
        self.assertEquals(line.purchase_id, purchase)
