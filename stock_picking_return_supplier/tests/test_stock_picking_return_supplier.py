###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import exceptions, fields
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
        self.customer_02 = self.env['res.partner'].create({
            'name': 'Test customer 2',
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
        self.warehouse = self.env.ref('stock.warehouse0')
        self.picking_type_dropshipping = self.env.ref(
            'stock_dropshipping.picking_type_dropship')
        self.dropshipping_route = self.env.ref(
            'stock_dropshipping.route_drop_shipping')
        self.product_dropshipping = self.env['product.product'].create({
            'name': 'Test product dropshipping',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.dropshipping_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 10,
            })],
        })
        self.product_dropshipping_02 = self.env['product.product'].create({
            'name': 'Test product dropshipping 2',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.dropshipping_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 5,
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
            'date': fields.Date.today(),
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'location_dest_id': self.supplier_loc.id,
            'picking_type': self.picking_type.id,
        })
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'product_id': self.product_dropshipping.id,
            'partner_id': self.customer.id,
            'purchase_id': purchase.id,
        })
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.line_ids[0].wizard_id, wizard)
        self.assertEquals(
            wizard.line_ids[0].product_id, self.product_dropshipping)
        self.assertEquals(wizard.line_ids[0].partner_id, self.customer)
        self.assertFalse(wizard.line_ids[0].sale_id)
        self.assertEquals(wizard.line_ids[0].purchase_id, purchase)
        self.assertEquals(len(wizard.confirm_line_ids), 0)
        wizard.button_assign()
        self.assertEquals(len(wizard.confirm_line_ids), 1)
        self.assertEquals(wizard.confirm_line_ids[0].wizard_id, wizard)
        self.assertEquals(
            wizard.confirm_line_ids[0].picking_id, purchase.picking_ids[0])
        self.assertEquals(
            wizard.confirm_line_ids[0].product_id, self.product_dropshipping)
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 0)
        self.assertEquals(wizard.confirm_line_ids[0].qty_available, 1)
        self.assertEquals(
            wizard.confirm_line_ids[0].move_id, picking_ret.move_lines[0])
        self.assertEquals(
            wizard.confirm_line_ids[0].wizard_line, wizard.line_ids[0])
        self.assertEquals(
            wizard.confirm_line_ids[0].line_ref, wizard.line_ids[0].id)
        wizard.confirm_line_ids[0].write({
            'qty_request': 1,
        })
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 1)
        res = wizard.button_accept()
        picking_supplier = self.env['stock.picking'].browse(res['res_id'])
        self.assertEquals(picking_supplier.partner_id, wizard.partner_id)
        self.assertEquals(
            picking_supplier.picking_type_id, wizard.picking_type)
        self.assertEquals(picking_supplier.location_id, wizard.location_id)
        self.assertEquals(
            picking_supplier.location_dest_id, wizard.location_dest_id)
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
            wizard.location_dest_id)
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
            'date': fields.Date.today(),
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'location_dest_id': self.supplier_loc.id,
            'picking_type': self.picking_type.id,
        })
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'product_id': self.product_dropshipping.id,
            'partner_id': self.customer.id,
            'sale_id': sale.id,
        })
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.line_ids[0].wizard_id, wizard)
        self.assertEquals(
            wizard.line_ids[0].product_id, self.product_dropshipping)
        self.assertEquals(wizard.line_ids[0].partner_id, self.customer)
        self.assertFalse(wizard.line_ids[0].purchase_id)
        self.assertEquals(wizard.line_ids[0].sale_id, sale)
        self.assertEquals(len(wizard.confirm_line_ids), 0)
        wizard.button_assign()
        self.assertEquals(len(wizard.confirm_line_ids), 1)
        self.assertEquals(wizard.confirm_line_ids[0].wizard_id, wizard)
        self.assertEquals(
            wizard.confirm_line_ids[0].picking_id, purchase.picking_ids[0])
        self.assertEquals(
            wizard.confirm_line_ids[0].product_id, self.product_dropshipping)
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 0)
        self.assertEquals(wizard.confirm_line_ids[0].qty_available, 1)
        self.assertEquals(
            wizard.confirm_line_ids[0].move_id, picking_ret.move_lines[0])
        self.assertEquals(
            wizard.confirm_line_ids[0].wizard_line, wizard.line_ids[0])
        self.assertEquals(
            wizard.confirm_line_ids[0].line_ref, wizard.line_ids[0].id)
        wizard.confirm_line_ids[0].write({
            'qty_request': 1,
        })
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 1)
        res = wizard.button_accept()
        picking_supplier = self.env['stock.picking'].browse(res['res_id'])
        self.assertEquals(picking_supplier.partner_id, wizard.partner_id)
        self.assertEquals(
            picking_supplier.picking_type_id, wizard.picking_type)
        self.assertEquals(picking_supplier.location_id, wizard.location_id)
        self.assertEquals(
            picking_supplier.location_dest_id, wizard.location_dest_id)
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
            wizard.location_dest_id)
        self.assertEquals(purchase.order_line[0].qty_received, 1)
        self.assertEquals(picking_supplier.picking_count, 1)
        self.assertEquals(picking_supplier.purchase_count, 1)
        res = picking_supplier.action_view_picking_purchase_link()
        self.assertEquals(res['domain'], [('id', 'in', purchase.ids)])
        self.assertEquals(res['res_id'], purchase.id)
        res = picking_supplier.action_view_picking_origin_move_link()
        self.assertEquals(res['domain'], [('id', 'in', picking_ret.ids)])
        self.assertEquals(res['res_id'], picking_ret.id)

    def test_standard_mtd_multiple_purchase(self):
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale_01 = self.create_sale(
            self.product_dropshipping, 1, self.warehouse, self.customer)
        self.assertEquals(sale_01.state, 'sale')
        sale_02 = self.create_sale(
            self.product_dropshipping_02, 1, self.warehouse, self.customer_02)
        self.assertEquals(sale_02.state, 'sale')
        self.assertNotEquals(sale_01.partner_id, sale_02.partner_id)
        self.assertEquals(len(sale_01.picking_ids), 0)
        self.assertEquals(len(sale_02.picking_ids), 0)
        purchase_01 = self.env['purchase.order'].search([
            ('group_id', '=', sale_01.procurement_group_id.id),
        ])
        purchase_02 = self.env['purchase.order'].search([
            ('group_id', '=', sale_02.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase_01), 1)
        self.assertEquals(len(purchase_02), 1)
        self.assertEquals(purchase_01.state, 'draft')
        self.assertEquals(purchase_02.state, 'draft')
        self.assertEquals(len(purchase_01.order_line), 1)
        self.assertEquals(len(purchase_02.order_line), 1)
        self.assertEquals(purchase_01.order_line.product_uom_qty, 1)
        self.assertEquals(purchase_02.order_line.product_uom_qty, 1)
        purchase_01.button_confirm()
        purchase_02.button_confirm()
        self.assertEquals(len(sale_01.picking_ids), 1)
        self.assertEquals(len(purchase_01.picking_ids), 1)
        self.assertEquals(len(sale_02.picking_ids), 1)
        self.assertEquals(len(purchase_02.picking_ids), 1)
        purchase_picking_01 = purchase_01.picking_ids
        purchase_picking_02 = purchase_02.picking_ids
        self.picking_transfer(purchase_picking_01, qty=1)
        self.picking_transfer(purchase_picking_02, qty=1)
        self.assertEquals(purchase_picking_01.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking_02.location_id, self.supplier_loc)
        self.assertEquals(
            purchase_picking_01.location_dest_id, self.customer_loc)
        self.assertEquals(
            purchase_picking_02.location_dest_id, self.customer_loc)
        self.assertEquals(sale_01.order_line[0].qty_delivered, 1)
        self.assertEquals(sale_02.order_line[0].qty_delivered, 1)
        self.assertEquals(purchase_picking_01.state, 'done')
        self.assertEquals(purchase_picking_02.state, 'done')
        return_picking_01 = self.env['stock.return.picking'].with_context(
            active_ids=purchase_picking_01.ids,
            active_id=purchase_picking_01.ids[0],
        ).create({})
        return_picking_01.location_id = self.location_test.id
        return_picking_01.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking_01.create_returns()
        return_picking_02 = self.env['stock.return.picking'].with_context(
            active_ids=purchase_picking_02.ids,
            active_id=purchase_picking_02.ids[0],
        ).create({})
        return_picking_02.location_id = self.location_test.id
        return_picking_02.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking_02.create_returns()
        picking_ret_01 = sale_01.picking_ids[0]
        self.picking_transfer(picking_ret_01, 1)
        self.assertEquals(len(sale_01.picking_ids), 2)
        self.assertEquals(len(purchase_01.picking_ids), 2)
        picking_ret_02 = sale_02.picking_ids[0]
        self.picking_transfer(picking_ret_02, 1)
        self.assertEquals(len(sale_02.picking_ids), 2)
        self.assertEquals(len(purchase_02.picking_ids), 2)
        wizard = self.env['stock.picking.return.supplier'].create({
            'date': fields.Date.today(),
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'location_dest_id': self.supplier_loc.id,
            'picking_type': self.picking_type.id,
        })
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'product_id': self.product_dropshipping.id,
            'partner_id': self.customer.id,
            'purchase_id': purchase_01.id,
        })
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'product_id': self.product_dropshipping_02.id,
            'partner_id': self.customer_02.id,
            'purchase_id': purchase_02.id,
        })
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertFalse(wizard.line_ids[0].sale_id)
        self.assertFalse(wizard.line_ids[1].sale_id)
        self.assertEquals(len(wizard.confirm_line_ids), 0)
        wizard.button_assign()
        self.assertEquals(len(wizard.confirm_line_ids), 2)
        wizard.confirm_line_ids[0].write({
            'qty_request': 1,
        })
        wizard.confirm_line_ids[1].write({
            'qty_request': 1,
        })
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 1)
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 1)
        res = wizard.button_accept()
        picking_supplier = self.env['stock.picking'].browse(res['res_id'])
        self.assertEquals(picking_supplier.partner_id, wizard.partner_id)
        self.assertEquals(
            picking_supplier.picking_type_id, wizard.picking_type)
        self.assertEquals(picking_supplier.location_id, wizard.location_id)
        self.assertEquals(
            picking_supplier.location_dest_id, wizard.location_dest_id)
        self.assertEquals(len(picking_supplier.move_lines), 2)
        move_01 = picking_supplier.move_lines.filtered(
            lambda m: m.product_id == self.product_dropshipping)
        move_02 = picking_supplier.move_lines.filtered(
            lambda m: m.product_id == self.product_dropshipping_02)
        self.assertEquals(
            move_01.product_id,
            self.product_dropshipping)
        self.assertEquals(
            move_02.product_id,
            self.product_dropshipping_02)
        self.assertEquals(move_01.product_uom_qty, 1)
        self.assertEquals(move_02.product_uom_qty, 1)
        self.assertEquals(purchase_01.order_line[0].qty_received, 1)
        self.assertEquals(purchase_02.order_line[0].qty_received, 1)
        self.assertEquals(picking_supplier.picking_count, 2)
        self.assertEquals(picking_supplier.purchase_count, 2)
        res = picking_supplier.action_view_picking_purchase_link()
        self.assertIn(purchase_01.id, res['domain'][0][2])
        self.assertIn(purchase_02.id, res['domain'][0][2])
        res = picking_supplier.action_view_picking_origin_move_link()
        self.assertIn(picking_ret_01.id, res['domain'][0][2])
        self.assertIn(picking_ret_02.id, res['domain'][0][2])

    def test_standard_mtd_multiple_sale(self):
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale_01 = self.create_sale(
            self.product_dropshipping, 1, self.warehouse, self.customer)
        self.assertEquals(sale_01.state, 'sale')
        sale_02 = self.create_sale(
            self.product_dropshipping_02, 1, self.warehouse, self.customer_02)
        self.assertEquals(sale_02.state, 'sale')
        self.assertNotEquals(sale_01.partner_id, sale_02.partner_id)
        self.assertEquals(len(sale_01.picking_ids), 0)
        self.assertEquals(len(sale_02.picking_ids), 0)
        purchase_01 = self.env['purchase.order'].search([
            ('group_id', '=', sale_01.procurement_group_id.id),
        ])
        purchase_02 = self.env['purchase.order'].search([
            ('group_id', '=', sale_02.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase_01), 1)
        self.assertEquals(len(purchase_02), 1)
        self.assertEquals(purchase_01.state, 'draft')
        self.assertEquals(purchase_02.state, 'draft')
        self.assertEquals(len(purchase_01.order_line), 1)
        self.assertEquals(len(purchase_02.order_line), 1)
        self.assertEquals(purchase_01.order_line.product_uom_qty, 1)
        self.assertEquals(purchase_02.order_line.product_uom_qty, 1)
        purchase_01.button_confirm()
        purchase_02.button_confirm()
        self.assertEquals(len(sale_01.picking_ids), 1)
        self.assertEquals(len(purchase_01.picking_ids), 1)
        self.assertEquals(len(sale_02.picking_ids), 1)
        self.assertEquals(len(purchase_02.picking_ids), 1)
        purchase_picking_01 = purchase_01.picking_ids
        purchase_picking_02 = purchase_02.picking_ids
        self.picking_transfer(purchase_picking_01, qty=1)
        self.picking_transfer(purchase_picking_02, qty=1)
        self.assertEquals(purchase_picking_01.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking_02.location_id, self.supplier_loc)
        self.assertEquals(
            purchase_picking_01.location_dest_id, self.customer_loc)
        self.assertEquals(
            purchase_picking_02.location_dest_id, self.customer_loc)
        self.assertEquals(sale_01.order_line[0].qty_delivered, 1)
        self.assertEquals(sale_02.order_line[0].qty_delivered, 1)
        self.assertEquals(purchase_picking_01.state, 'done')
        self.assertEquals(purchase_picking_02.state, 'done')
        return_picking_01 = self.env['stock.return.picking'].with_context(
            active_ids=purchase_picking_01.ids,
            active_id=purchase_picking_01.ids[0],
        ).create({})
        return_picking_01.location_id = self.location_test.id
        return_picking_01.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking_01.create_returns()
        return_picking_02 = self.env['stock.return.picking'].with_context(
            active_ids=purchase_picking_02.ids,
            active_id=purchase_picking_02.ids[0],
        ).create({})
        return_picking_02.location_id = self.location_test.id
        return_picking_02.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking_02.create_returns()
        picking_ret_01 = sale_01.picking_ids[0]
        self.picking_transfer(picking_ret_01, 1)
        self.assertEquals(len(sale_01.picking_ids), 2)
        self.assertEquals(len(purchase_01.picking_ids), 2)
        picking_ret_02 = sale_02.picking_ids[0]
        self.picking_transfer(picking_ret_02, 1)
        self.assertEquals(len(sale_02.picking_ids), 2)
        self.assertEquals(len(purchase_02.picking_ids), 2)
        self.assertEquals(sale_01.order_line[0].qty_delivered, 0)
        self.assertEquals(sale_02.order_line[0].qty_delivered, 0)
        wizard = self.env['stock.picking.return.supplier'].create({
            'date': fields.Date.today(),
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'location_dest_id': self.supplier_loc.id,
            'picking_type': self.picking_type.id,
        })
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'product_id': self.product_dropshipping.id,
            'partner_id': self.customer.id,
            'sale_id': sale_01.id,
        })
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'product_id': self.product_dropshipping_02.id,
            'partner_id': self.customer_02.id,
            'sale_id': sale_02.id,
        })
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertFalse(wizard.line_ids[0].purchase_id)
        self.assertFalse(wizard.line_ids[1].purchase_id)
        self.assertEquals(len(wizard.confirm_line_ids), 0)
        wizard.button_assign()
        self.assertEquals(len(wizard.confirm_line_ids), 2)
        wizard.confirm_line_ids[0].write({
            'qty_request': 1,
        })
        wizard.confirm_line_ids[1].write({
            'qty_request': 1,
        })
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 1)
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 1)
        res = wizard.button_accept()
        picking_supplier = self.env['stock.picking'].browse(res['res_id'])
        self.assertEquals(picking_supplier.partner_id, wizard.partner_id)
        self.assertEquals(
            picking_supplier.picking_type_id, wizard.picking_type)
        self.assertEquals(picking_supplier.location_id, wizard.location_id)
        self.assertEquals(
            picking_supplier.location_dest_id, wizard.location_dest_id)
        self.assertEquals(len(picking_supplier.move_lines), 2)
        move_01 = picking_supplier.move_lines.filtered(
            lambda m: m.product_id == self.product_dropshipping)
        move_02 = picking_supplier.move_lines.filtered(
            lambda m: m.product_id == self.product_dropshipping_02)
        self.assertEquals(
            move_01.product_id,
            self.product_dropshipping)
        self.assertEquals(
            move_02.product_id,
            self.product_dropshipping_02)
        self.assertEquals(move_01.product_uom_qty, 1)
        self.assertEquals(move_02.product_uom_qty, 1)
        self.assertEquals(purchase_01.order_line[0].qty_received, 1)
        self.assertEquals(purchase_02.order_line[0].qty_received, 1)
        self.assertEquals(picking_supplier.picking_count, 2)
        self.assertEquals(picking_supplier.purchase_count, 2)
        res = picking_supplier.action_view_picking_purchase_link()
        self.assertIn(purchase_01.id, res['domain'][0][2])
        self.assertIn(purchase_02.id, res['domain'][0][2])
        res = picking_supplier.action_view_picking_origin_move_link()
        self.assertIn(picking_ret_01.id, res['domain'][0][2])
        self.assertIn(picking_ret_02.id, res['domain'][0][2])

    def test_standard_mtd_only_product_and_partner(self):
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
        purchase.button_confirm()
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(len(purchase.picking_ids), 1)
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=1)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking.location_dest_id, self.customer_loc)
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
        self.assertEquals(sale.order_line[0].qty_delivered, 0)
        wizard = self.env['stock.picking.return.supplier'].create({
            'date': fields.Date.today(),
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'location_dest_id': self.supplier_loc.id,
            'picking_type': self.picking_type.id,
        })
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'product_id': self.product_dropshipping.id,
            'partner_id': self.customer.id,
        })
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertFalse(wizard.line_ids[0].purchase_id)
        self.assertFalse(wizard.line_ids[0].sale_id)
        self.assertEquals(len(wizard.confirm_line_ids), 0)
        wizard.button_assign()
        self.assertEquals(len(wizard.confirm_line_ids), 1)
        self.assertEquals(
            wizard.confirm_line_ids[0].product_id, self.product_dropshipping)
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 0)
        self.assertEquals(wizard.confirm_line_ids[0].qty_available, 1)
        self.assertEquals(
            wizard.confirm_line_ids[0].move_id, picking_ret.move_lines[0])
        self.assertEquals(
            wizard.confirm_line_ids[0].wizard_line, wizard.line_ids[0])
        wizard.confirm_line_ids[0].write({
            'qty_request': 1,
        })
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 1)
        res = wizard.button_accept()
        picking_supplier = self.env['stock.picking'].browse(res['res_id'])
        self.assertEquals(picking_supplier.partner_id, wizard.partner_id)
        self.assertEquals(picking_supplier.location_id, wizard.location_id)
        self.assertEquals(
            picking_supplier.location_dest_id, wizard.location_dest_id)
        self.assertEquals(len(picking_supplier.move_lines), 1)
        self.assertEquals(
            picking_supplier.move_lines[0].product_id,
            self.product_dropshipping)
        self.assertEquals(picking_supplier.move_lines[0].product_uom_qty, 1)
        self.assertEquals(purchase.order_line[0].qty_received, 1)
        self.assertEquals(picking_supplier.picking_count, 1)
        self.assertEquals(picking_supplier.purchase_count, 1)
        res = picking_supplier.action_view_picking_purchase_link()
        self.assertEquals(res['domain'], [('id', 'in', purchase.ids)])
        self.assertEquals(res['res_id'], purchase.id)
        res = picking_supplier.action_view_picking_origin_move_link()
        self.assertEquals(res['domain'], [('id', 'in', picking_ret.ids)])
        self.assertEquals(res['res_id'], picking_ret.id)

    def test_standard_mtd_partial_stock(self):
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(
            self.product_dropshipping, 3, self.warehouse, self.customer)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 0)
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        purchase.button_confirm()
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(len(purchase.picking_ids), 1)
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=3)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking.location_dest_id, self.customer_loc)
        self.assertEquals(sale.order_line[0].qty_delivered, 3)
        self.assertEquals(purchase_picking.state, 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=purchase_picking.ids,
            active_id=purchase_picking.ids[0],
        ).create({})
        return_picking.location_id = self.location_test.id
        return_picking.product_return_moves.write({
            'quantity': 2.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        picking_ret = sale.picking_ids[0]
        self.picking_transfer(picking_ret, 2)
        self.assertEquals(sale.order_line[0].qty_delivered, 1)
        wizard = self.env['stock.picking.return.supplier'].create({
            'date': fields.Date.today(),
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'location_dest_id': self.supplier_loc.id,
            'picking_type': self.picking_type.id,
        })
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'product_id': self.product_dropshipping.id,
            'partner_id': self.customer.id,
            'purchase_id': purchase.id,
        })
        wizard.button_assign()
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 0)
        self.assertEquals(wizard.confirm_line_ids[0].qty_available, 2)
        qty_available_01 = wizard.confirm_line_ids[0].qty_available
        wizard.confirm_line_ids[0].write({
            'qty_request': 1,
        })
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 1)
        res = wizard.button_accept()
        picking_supplier = self.env['stock.picking'].browse(res['res_id'])
        self.assertEquals(picking_supplier.partner_id, wizard.partner_id)
        self.assertEquals(picking_supplier.location_id, wizard.location_id)
        self.assertEquals(
            picking_supplier.location_dest_id, wizard.location_dest_id)
        self.assertEquals(
            picking_supplier.move_lines[0].product_id,
            self.product_dropshipping)
        self.assertEquals(picking_supplier.move_lines[0].product_uom_qty, 1)
        self.picking_transfer(picking_supplier, 1)
        self.assertEquals(picking_supplier.state, 'done')
        self.assertEquals(sale.order_line[0].qty_delivered, 1)
        self.assertEquals(picking_supplier.picking_count, 1)
        self.assertEquals(picking_supplier.purchase_count, 1)
        res = picking_supplier.action_view_picking_purchase_link()
        self.assertEquals(res['domain'], [('id', 'in', purchase.ids)])
        self.assertEquals(res['res_id'], purchase.id)
        res = picking_supplier.action_view_picking_origin_move_link()
        self.assertEquals(res['domain'], [('id', 'in', picking_ret.ids)])
        self.assertEquals(res['res_id'], picking_ret.id)
        wizard_02 = self.env['stock.picking.return.supplier'].create({
            'date': fields.Date.today(),
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'location_dest_id': self.supplier_loc.id,
            'picking_type': self.picking_type.id,
        })
        wizard_02.line_ids.create({
            'wizard_id': wizard_02.id,
            'product_id': self.product_dropshipping.id,
            'partner_id': self.customer.id,
            'purchase_id': purchase.id,
        })
        wizard_02.button_assign()
        self.assertEquals(len(wizard_02.confirm_line_ids), 1)
        self.assertEquals(
            wizard_02.confirm_line_ids[0].product_id,
            self.product_dropshipping)
        self.assertEquals(wizard_02.confirm_line_ids[0].qty_request, 0)
        self.assertEquals(wizard_02.confirm_line_ids[0].qty_available, 1)
        qty_available_02 = wizard_02.confirm_line_ids[0].qty_available
        self.assertNotEquals(qty_available_01, qty_available_02)
        self.assertEquals(
            qty_available_02,
            qty_available_01 - wizard.confirm_line_ids[0].qty_request)
        self.assertEquals(purchase.order_line[0].qty_received, 2)

    def test_standard_mtd_no_picking_done(self):
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(
            self.product_dropshipping, 1, self.warehouse, self.customer)
        self.assertEquals(sale.state, 'sale')
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        purchase.button_confirm()
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=1)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking.location_dest_id, self.customer_loc)
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
        wizard = self.env['stock.picking.return.supplier'].create({
            'date': fields.Date.today(),
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'location_dest_id': self.supplier_loc.id,
            'picking_type': self.picking_type.id,
        })
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'product_id': self.product_dropshipping.id,
            'partner_id': self.customer.id,
            'purchase_id': purchase.id,
        })
        wizard.button_assign()
        self.assertEquals(len(wizard.confirm_line_ids), 0)
        picking_ret = sale.picking_ids[0]
        self.picking_transfer(picking_ret, 1)
        self.assertEquals(picking_ret.state, 'done')
        wizard.button_assign()
        self.assertEquals(len(wizard.confirm_line_ids), 1)
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 0)
        self.assertEquals(wizard.confirm_line_ids[0].qty_available, 1)

    def test_standard_mtd_route_check_quantities(self):
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(
            self.product_dropshipping, 1, self.warehouse, self.customer)
        self.assertEquals(sale.state, 'sale')
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        purchase.button_confirm()
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=1)
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
            'quantity': 1,
            'to_refund': True,
        })
        return_picking.create_returns()
        picking_ret = sale.picking_ids[0]
        self.picking_transfer(picking_ret, 1)
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(len(purchase.picking_ids), 2)
        wizard = self.env['stock.picking.return.supplier'].create({
            'date': fields.Date.today(),
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'location_dest_id': self.supplier_loc.id,
            'picking_type': self.picking_type.id,
        })
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'product_id': self.product_dropshipping.id,
            'partner_id': self.customer.id,
            'purchase_id': purchase.id,
        })
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(
            wizard.line_ids[0].product_id, self.product_dropshipping)
        self.assertEquals(wizard.line_ids[0].partner_id, self.customer)
        self.assertFalse(wizard.line_ids[0].sale_id)
        self.assertEquals(wizard.line_ids[0].purchase_id, purchase)
        self.assertEquals(len(wizard.confirm_line_ids), 0)
        wizard.button_assign()
        self.assertEquals(len(wizard.confirm_line_ids), 1)
        self.assertEquals(
            wizard.confirm_line_ids[0].product_id, self.product_dropshipping)
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 0)
        self.assertEquals(wizard.confirm_line_ids[0].qty_available, 1)
        wizard.confirm_line_ids[0].write({
            'qty_request': 2,
        })
        self.assertEquals(wizard.confirm_line_ids[0].qty_request, 2)
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.button_accept()
        self.assertEquals(
            result.exception.name,
            'The selected quantity for product [%s] exceeds '
            'the quantity available' % self.product_dropshipping.default_code)

    def test_filter_by_date(self):
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
        picking_ret.date_done = fields.Datetime.now() - timedelta(days=1)
        wizard = self.env['stock.picking.return.supplier'].create({
            'date': fields.Date.today(),
            'filter_by_date': True,
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'location_dest_id': self.supplier_loc.id,
            'picking_type': self.picking_type.id,
        })
        self.assertTrue(wizard.filter_by_date)
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'product_id': self.product_dropshipping.id,
            'partner_id': self.customer.id,
            'purchase_id': purchase.id,
        })
        wizard.button_assign()
        self.assertEquals(len(wizard.confirm_line_ids), 0)

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
            'date': fields.Date.today(),
            'filter_by_date': True,
            'partner_id': self.supplier.id,
            'location_id': self.location_test.id,
            'location_dest_id': self.supplier_loc.id,
            'picking_type': self.picking_type.id,
        })
        wizard.line_ids.create({
            'wizard_id': wizard.id,
            'product_id': self.product_dropshipping.id,
            'partner_id': self.customer.id,
            'purchase_id': purchase.id,
        })
        self.assertEquals(len(wizard.line_ids), 1)
        wizard.button_assign()
        self.assertEquals(len(wizard.confirm_line_ids), 1)
        wizard.button_delete_lines()
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(len(wizard.confirm_line_ids), 0)
