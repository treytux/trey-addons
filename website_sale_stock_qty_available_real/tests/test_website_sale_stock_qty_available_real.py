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
            'tracking': 'none',
        })
        self.location = self.env.ref('stock.stock_location_stock')
        self.supplier_location = self.env.ref('stock.stock_location_suppliers')
        self.available_website = self.env['website'].create({
            'name': 'Available stock website',
        })
        self.real_website = self.env['website'].create({
            'name': 'Real stock website',
            'website_sale_stock_qty_mode': 'real',
        })
        self.forecasted_website = self.env['website'].create({
            'name': 'Forecasted stock website',
            'website_sale_stock_qty_mode': 'forecasted',
        })

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
        self.assertEqual(
            qty_dict[self.product.id]['free_qty'],
            self.product.qty_available_real)
        product_uom_qty = 10
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': product_uom_qty})],
        })
        sale.action_confirm()
        qty_dict = self.product._compute_quantities_dict(
            lot_id=False, owner_id=False, package_id=False)
        self.assertEqual(
            qty_dict[self.product.id]['virtual_available'],
            quantity - product_uom_qty)
        self.assertEqual(
            qty_dict[self.product.id]['free_qty'],
            self.product.qty_available_real)
        self.assertEqual(self.product.qty_available, quantity)
        self.assertEqual(
            self.product.qty_available_real,
            quantity - product_uom_qty)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        self.assertEqual(
            self.product.qty_available,
            self.product.qty_available_real)
        qty_dict = self.product._compute_quantities_dict(
            lot_id=False, owner_id=False, package_id=False)
        self.assertEqual(
            qty_dict[self.product.id]['virtual_available'],
            self.product.qty_available_real)
        self.assertEqual(
            qty_dict[self.product.id]['free_qty'],
            self.product.qty_available_real)

    def test_context_switches_sale_stock_quantities_by_mode(self):
        self.env['stock.move'].create({
            'name': 'Incoming forecast stock',
            'product_id': self.product.id,
            'product_uom_qty': 5.0,
            'product_uom': self.product.uom_id.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.location.id,
        })._action_confirm()
        self.product.invalidate_recordset([
            'qty_available',
            'qty_available_real',
            'virtual_available',
        ])
        self.assertEqual(self.product.qty_available, 0.0)
        self.assertEqual(self.product.qty_available_real, 0.0)
        qty_dict = self.product._compute_quantities_dict(
            lot_id=False, owner_id=False, package_id=False)
        self.assertEqual(
            qty_dict[self.product.id]['virtual_available'], 5.0)
        self.assertEqual(qty_dict[self.product.id]['free_qty'], 0.0)
        real_product = self.product.with_context(
            website_sale_stock_qty_mode='real')
        qty_dict = real_product._compute_quantities_dict(
            lot_id=False, owner_id=False, package_id=False)
        self.assertEqual(
            qty_dict[self.product.id]['virtual_available'], 0.0)
        self.assertEqual(qty_dict[self.product.id]['free_qty'], 0.0)
        forecasted_product = self.product.with_context(
            website_sale_stock_qty_mode='forecasted')
        qty_dict = forecasted_product._compute_quantities_dict(
            lot_id=False, owner_id=False, package_id=False)
        self.assertEqual(
            qty_dict[self.product.id]['virtual_available'], 5.0)
        self.assertEqual(qty_dict[self.product.id]['free_qty'], 5.0)

    def test_setting_is_stored_per_website(self):
        settings = self.env['res.config.settings'].create({
            'website_id': self.available_website.id,
        })
        settings.website_sale_stock_qty_mode = 'forecasted'
        self.assertEqual(
            self.available_website.website_sale_stock_qty_mode,
            'forecasted')
        self.assertEqual(
            self.real_website.website_sale_stock_qty_mode, 'real')
        self.available_website.website_sale_stock_qty_mode = 'available'
        self.assertEqual(
            self.available_website.website_sale_stock_qty_mode,
            'available')
        self.assertEqual(
            self.real_website.website_sale_stock_qty_mode, 'real')

    def test_order_context_depends_on_website_setting(self):
        available_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'website_id': self.available_website.id,
        })
        real_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'website_id': self.real_website.id,
        })
        forecasted_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'website_id': self.forecasted_website.id,
        })
        self.assertNotIn(
            'website_sale_stock_qty_mode',
            available_order._get_context_for_line(
                self.env['sale.order.line']))
        self.assertEqual(
            real_order._get_context_for_line(
                self.env['sale.order.line'])['website_sale_stock_qty_mode'],
            'real')
        self.assertEqual(
            forecasted_order._get_context_for_line(
                self.env['sale.order.line'])['website_sale_stock_qty_mode'],
            'forecasted')
