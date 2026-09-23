###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestStockDropshippingFix(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.warehouse = self.env.ref('stock.warehouse0')
        self.customer_loc = self.env.ref('stock.stock_location_customers')
        self.supplier_loc = self.env.ref('stock.stock_location_suppliers')
        self.dropshipping_route = self.env.ref(
            'stock_dropshipping.route_drop_shipping')
        self.customer = self.env['res.partner'].create({
            'name': 'Test customer',
            'company_id': self.company.id,
        })
        self.supplier = self.env['res.partner'].create({
            'name': 'Test supplier',
            'company_id': self.company.id,
        })
        self.product_dropshipping = self.env['product.product'].create({
            'name': 'Test product dropshipping',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.dropshipping_route.id])],
            'seller_ids': [(0, 0, {
                'partner_id': self.supplier.id,
                'price': 10,
            })],
        })

    def update_qty_on_hand(self, product, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_id': product.id,
            'new_quantity': new_qty,
        })
        wizard.change_product_qty()

    def create_sale(self, product, quantity, warehouse):
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
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
        for move in picking.move_ids:
            move.quantity_done = qty
        picking.button_validate()
        self.assertEqual(picking.state, 'done')

    def test_sale_purchase_dropshipping(self):
        self.update_qty_on_hand(
            self.product_dropshipping, 10)
        sale = self.create_sale(self.product_dropshipping, 1, self.warehouse)
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 0)
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.state, 'draft')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line[0].product_uom_qty, 1)
        purchase.button_confirm()
        self.assertEqual(len(purchase.picking_ids), 1)
        self.assertEqual(len(sale.picking_ids), 1)
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=1)
        self.assertTrue(purchase_picking.is_dropship)
        self.assertEqual(purchase_picking.location_id, self.supplier_loc)
        self.assertEqual(purchase_picking.location_dest_id, self.customer_loc)
        self.assertNotEqual(purchase_picking.partner_id, purchase.partner_id)
        self.assertEqual(purchase_picking.partner_id, sale.partner_id)
        self.assertEqual(purchase_picking.supplier_id, purchase.partner_id)
        self.assertEqual(sale.picking_ids, purchase.picking_ids)
        self.assertEqual(
            sale.order_line[0].purchase_line_ids, purchase.order_line[0])
        self.assertEqual(sale.order_line[0].qty_delivered, 1)
