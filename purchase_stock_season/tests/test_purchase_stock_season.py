###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPurchaseStockSeason(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        supplier = self.env['res.partner'].create({
            'name': 'Test supplier',
            'is_company': True,
            'supplier': True,
        })
        buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.product_a = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test A',
            'route_ids': [(6, 0, buy_route.ids)],
            'seller_ids': [(0, 0, {
                'name': supplier.id,
                'price': 100.00,
            })],
        })
        warehouse = self.env.ref('stock.warehouse0')
        self.orderpoint = self.env['stock.warehouse.orderpoint'].create({
            'warehouse_id': warehouse.id,
            'location_id': warehouse.lot_stock_id.id,
            'product_id': self.product_a.id,
            'product_min_qty': 10.00,
            'product_max_qty': 20.00,
            'qty_multiple': 1,
            'lead_days': 1,
            'lead_type': 'supplier',
        })

    def test_check_purchse_orderpoint(self):
        self.env['procurement.group'].run_scheduler()
        purchase_order = self.env['purchase.order'].search([
            ('origin', 'ilike', self.orderpoint.name),
        ])
        self.assertEquals(len(purchase_order), 1)
        self.assertEquals(len(purchase_order.order_line), 1)
        self.assertEqual(
            purchase_order.order_line[0].product_qty, 20)
        self.assertIn(self.orderpoint.name, purchase_order.origin)
        self.assertFalse(purchase_order.is_season)
        mto_route = self.env.ref('stock.route_warehouse0_mto')
        mto_route.is_season = True
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'is_season': True,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_qty': 10,
                    'route_id': mto_route.id,
                }),
            ],
        })
        sale.action_confirm()
        purchase_order = self.env['purchase.order'].search([
            ('origin', 'ilike', sale.name),
        ])
        self.assertEquals(len(purchase_order), 1)
        self.assertEquals(len(purchase_order.order_line), 1)
        self.assertEqual(
            purchase_order.order_line[0].product_id.id, self.product_a.id)
        self.assertEqual(
            purchase_order.order_line[0].product_qty, 10)
        self.assertIn(sale.name, purchase_order.origin)
        self.assertEqual(len(purchase_order.order_line[0].move_dest_ids), 1)
        self.assertEqual(
            purchase_order.order_line[0].move_dest_ids[0].sale_line_id.id,
            sale.order_line[0].id)
        self.assertTrue(purchase_order.is_season)
        self.assertEquals(purchase_order.sale_order_id.id, sale.id)
