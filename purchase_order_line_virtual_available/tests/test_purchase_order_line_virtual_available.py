###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestPurchaseOrderLineVirtualAvailable(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.warehouse_1 = self.env.ref('stock.warehouse0')
        self.stock_location = self.warehouse_1.lot_stock_id
        self.warehouse_2 = self.env['stock.warehouse'].create({
            'code': 'WH2',
            'name': 'Warehouse 2',
        })
        self.stock_location_2 = self.warehouse_2.lot_stock_id

    def test_purchase_order_line_virtual_available(self):
        quant = self.env['stock.quant']
        quant._update_available_quantity(
            self.product, self.stock_location, 10.0)
        quant._update_available_quantity(
            self.product, self.stock_location_2, 5.0)
        self.assertEqual(self.product.virtual_available, 15.0)
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.warehouse_1.in_type_id.id,
        })
        purchase.onchange_partner_id()
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': self.product.id,
            'product_qty': 20.0,
        })
        line.onchange_product_id()
        self.assertEqual(line.virtual_available, 10)
