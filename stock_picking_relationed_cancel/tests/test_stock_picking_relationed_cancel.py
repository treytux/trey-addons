###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestStockPickingRelationedCancel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.supplier = self.env['res.partner'].create({
            'name': 'Supplier test',
            'supplier': True,
        })
        self.customer = self.env['res.partner'].create({
            'name': 'Customer test',
            'customer': True,
        })
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.mto_route = self.env.ref('stock.route_warehouse0_mto')
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test 1',
            'standard_price': 10,
            'list_price': 100,
            'route_ids': [(6, 0, [self.buy_route.id, self.mto_route.id])],
        })
        self.env['product.supplierinfo'].create({
            'name': self.customer.id,
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'price': 80,
        })
        self.warehouse = self.env.ref('stock.warehouse0')
        self.env['stock.warehouse.orderpoint'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'product_id': self.product_01.id,
            'product_min_qty': 25.00,
            'product_max_qty': 50.00,
        })
        self.manager_user = self.env['res.users'].create({
            'name': 'Manager user',
            'login': 'manager@test.com',
            'groups_id': [
                (4, self.env.ref('sales_team.group_sale_manager').id),
                (4, self.env.ref('purchase.group_purchase_manager').id),
                (4, self.env.ref('stock.group_stock_manager').id),
                (4, self.env.ref('stock.group_stock_multi_warehouses').id),
            ],
        })
        self.manager_user.partner_id.email = self.manager_user.login

    def test_route_mto_default_not_allow(self):
        import logging
        _log = logging.getLogger(__name__)

        _log.info('t' * 80)
        self.mto_route.allow_cancel_picking_relationed = False
        self.assertEquals(
            self.mto_route.allow_cancel_picking_relationed, False)
        sale = self.env['sale.order'].sudo(self.manager_user).create({
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1,
                    'route_id': self.mto_route.id,
                }),
            ],
        })
        sale.sudo(self.manager_user).action_confirm()
        self.assertTrue(sale.picking_ids)
        picking_out = sale.picking_ids
        self.assertEquals(picking_out.state, 'waiting')
        purchase_line = self.env['purchase.order.line'].search([
            ('product_id', '=', self.product_01.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(purchase_line), 1)
        purchase = purchase_line.order_id
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase_line.product_qty, 1)
        purchase.sudo(self.manager_user).button_confirm()
        self.assertEquals(len(purchase.picking_ids), 1)
        picking_in = purchase.picking_ids
        self.assertEquals(picking_in.state, 'assigned')
        picking_in.sudo(self.manager_user).action_cancel()
        self.assertEquals(picking_in.state, 'cancel')
        self.assertEquals(picking_out.state, 'cancel')

    def test_route_allow(self):
        self.mto_route.allow_cancel_picking_relationed = True
        self.assertEquals(self.mto_route.allow_cancel_picking_relationed, True)
        sale = self.env['sale.order'].sudo(self.manager_user).create({
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1,
                    'route_id': self.mto_route.id,
                }),
            ],
        })
        sale.sudo(self.manager_user).action_confirm()
        self.assertTrue(sale.picking_ids)
        picking_out = sale.picking_ids
        self.assertEquals(picking_out.state, 'waiting')
        purchase_line = self.env['purchase.order.line'].search([
            ('product_id', '=', self.product_01.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(purchase_line), 1)
        purchase = purchase_line.order_id
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase_line.product_qty, 1)
        purchase.sudo(self.manager_user).button_confirm()
        self.assertEquals(len(purchase.picking_ids), 1)
        picking_in = purchase.picking_ids
        self.assertEquals(picking_in.state, 'assigned')
        picking_in.sudo(self.manager_user).action_cancel()
        self.assertEquals(picking_in.state, 'cancel')
        self.assertEquals(picking_out.state, 'confirmed')

    def test_route_allow_several_sales_confirmed(self):
        self.mto_route.allow_cancel_picking_relationed = True
        self.assertEquals(self.mto_route.allow_cancel_picking_relationed, True)
        sale1 = self.env['sale.order'].sudo(self.manager_user).create({
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1,
                    'route_id': self.mto_route.id,
                }),
            ],
        })
        sale1.sudo(self.manager_user).action_confirm()
        self.assertTrue(sale1.picking_ids)
        picking1_out = sale1.picking_ids
        self.assertEquals(picking1_out.state, 'waiting')
        sale2 = self.env['sale.order'].sudo(self.manager_user).create({
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 10,
                    'route_id': self.mto_route.id,
                }),
            ],
        })
        sale2.sudo(self.manager_user).action_confirm()
        self.assertTrue(sale2.picking_ids)
        picking2_out = sale2.picking_ids
        self.assertEquals(picking2_out.state, 'waiting')
        purchase_line = self.env['purchase.order.line'].search([
            ('product_id', '=', self.product_01.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(purchase_line), 1)
        self.assertEquals(purchase_line.product_qty, 11)
        purchase = purchase_line.order_id
        self.assertEquals(len(purchase), 1)
        purchase.sudo(self.manager_user).button_confirm()
        self.assertEquals(len(purchase.picking_ids), 1)
        picking_in = purchase.picking_ids
        self.assertEquals(picking_in.state, 'assigned')
        picking_in.sudo(self.manager_user).action_cancel()
        self.assertEquals(picking_in.state, 'cancel')
        self.assertEquals(picking1_out.state, 'confirmed')

    def test_route_allow_several_sales(self):
        self.mto_route.allow_cancel_picking_relationed = True
        self.assertEquals(self.mto_route.allow_cancel_picking_relationed, True)
        sale1 = self.env['sale.order'].sudo(self.manager_user).create({
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1,
                    'route_id': self.mto_route.id,
                }),
            ],
        })
        sale1.sudo(self.manager_user).action_confirm()
        self.assertTrue(sale1.picking_ids)
        picking1_out = sale1.picking_ids
        self.assertEquals(picking1_out.state, 'waiting')
        sale2 = self.env['sale.order'].sudo(self.manager_user).create({
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 10,
                    'route_id': self.mto_route.id,
                }),
            ],
        })
        sale2.sudo(self.manager_user).action_confirm()
        self.assertTrue(sale2.picking_ids)
        picking2_out = sale2.picking_ids
        self.assertEquals(picking2_out.state, 'waiting')
        purchase_line = self.env['purchase.order.line'].search([
            ('product_id', '=', self.product_01.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(purchase_line), 1)
        self.assertEquals(purchase_line.product_qty, 11)
        purchase = purchase_line.order_id
        self.assertEquals(len(purchase), 1)
        purchase.sudo(self.manager_user).button_confirm()
        self.assertEquals(len(purchase.picking_ids), 1)
        picking_in = purchase.picking_ids
        self.assertEquals(picking_in.state, 'assigned')
        picking_in.sudo(self.manager_user).action_cancel()
        self.assertEquals(picking_in.state, 'cancel')
        self.assertEquals(picking1_out.state, 'confirmed')
