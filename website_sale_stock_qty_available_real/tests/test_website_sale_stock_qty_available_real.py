###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestWebsiteSaleStockQtyAvailableReal(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.location = self.env.ref('stock.stock_location_stock')

    def test_product_qty_available_real(self):
        quantity = 100.0
        quant = self.env['stock.quant']
        quant._update_available_quantity(
            self.product, self.location, quantity)
        self.assertEqual(self.product.qty_available, quantity)
        self.assertEqual(self.product.qty_available_real, quantity)
        qty_dict = self.product._compute_quantities_dict(
            lot_id=False, owner_id=False, package_id=False)
        self.assertEqual(
            qty_dict[self.product.id]['virtual_available'],
            self.product.qty_available_real)
        product_uom_qty = 10
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': product_uom_qty})]
        })
        sale.action_confirm()
        qty_dict = self.product._compute_quantities_dict(
            lot_id=False, owner_id=False, package_id=False)
        self.assertEqual(
            qty_dict[self.product.id]['virtual_available'],
            quantity - product_uom_qty)
        self.assertEqual(self.product.qty_available, quantity)
        self.assertEqual(
            self.product.qty_available_real,
            quantity - product_uom_qty)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(
            self.product.qty_available,
            self.product.qty_available_real)
        qty_dict = self.product._compute_quantities_dict(
            lot_id=False, owner_id=False, package_id=False)
        self.assertEqual(
            qty_dict[self.product.id]['virtual_available'],
            self.product.qty_available_real)
