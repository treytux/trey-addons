###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase


class TestStockRouteSupplierSend(TransactionCase):

    def setUp(self):
        super().setUp()
        self.main_warehouse = self.env.ref('stock.warehouse0')
        self.picking_type_out = self.main_warehouse.out_type_id
        self.route_mto = self.env.ref('stock.route_warehouse0_mto')
        self.route_supplier_send = self.env.ref(
            'stock_route_supplier_send.route_supplier_send')
        self.supplier = self.env['res.partner'].create({
            'name': 'Supplier test',
            'supplier': True,
        })
        self.customer = self.env['res.partner'].create({
            'name': 'Customer test',
            'customer': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product',
            'standard_price': 10,
            'list_price': 100,
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 10,
            })],
        })

    def create_sale(self, partner, product):
        return self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
            ],
        })

    def test_normal_purchase(self):
        sale = self.create_sale(self.customer, self.product)
        self.assertFalse(sale.order_line.route_id)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids
        self.assertEqual(picking_out.picking_type_id, self.picking_type_out)
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('origin', '=', sale.name),
        ])
        self.assertEqual(len(purchase), 0)

    def test_purchase_mto_route(self):
        sale = self.create_sale(self.customer, self.product)
        sale.order_line.route_id = self.route_mto.id
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids
        self.assertEqual(picking_out.picking_type_id, self.picking_type_out)
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('origin', '=', sale.name),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertFalse(purchase.is_supplier_send)

    def test_supplier_send_workflow_01(self):
        sale = self.create_sale(self.customer, self.product)
        sale.order_line.route_id = self.route_supplier_send.id
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids
        self.assertEqual(picking_out.picking_type_id, self.picking_type_out)
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('origin', '=', sale.name),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertTrue(purchase.is_supplier_send)
        self.assertTrue(purchase.sale_id, sale)

    def test_supplier_send_workflow_02(self):
        purchase_test = self.env['purchase.order'].create({
            'partner_id': self.supplier.id,
            'order_line': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom': self.product.uom_po_id.id,
                    'price_unit': self.product.standard_price,
                    'product_qty': 1,
                    'date_planned': fields.Date.today(),
                }),
            ],
        })
        sale = self.create_sale(self.customer, self.product)
        sale.order_line.route_id = self.route_supplier_send.id
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids
        self.assertEqual(picking_out.picking_type_id, self.picking_type_out)
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('origin', '=', sale.name),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertNotEqual(purchase, purchase_test)
        self.assertTrue(purchase.is_supplier_send)
        self.assertTrue(purchase.sale_id, sale)

    def test_supplier_send_workflow_lines_with_different_routes(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2,
                    'route_id': self.route_mto.id,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 3,
                    'route_id': self.route_supplier_send.id,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids
        self.assertEqual(picking_out.picking_type_id, self.picking_type_out)
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('origin', '=', sale.name),
        ])
        self.assertEqual(len(purchase), 2)
        purchase_mto = purchase.filtered(
            lambda po: not po.is_supplier_send)
        self.assertFalse(purchase_mto.is_supplier_send)
        purchase_line_mto = purchase_mto.order_line.filtered(
            lambda ln: ln.product_qty == 2)
        self.assertEqual(len(purchase_line_mto), 1)
        purchase_supplier_send = purchase.filtered(
            lambda po: po.is_supplier_send)
        self.assertTrue(purchase_supplier_send.is_supplier_send)
        purchase_line_supplier_send = (
            purchase_supplier_send.order_line.filtered(
                lambda ln: ln.product_qty == 3))
        self.assertEqual(len(purchase_line_supplier_send), 1)
        self.assertTrue(purchase_supplier_send.sale_id, sale)
