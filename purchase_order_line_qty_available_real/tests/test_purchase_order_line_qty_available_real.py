###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests import common


class TestPurchaseOrderLineQtyAvailableReal(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 20,
            'list_price': 80,
        })
        self.location = self.env.ref('stock.stock_location_stock')
        self.location_dest = self.env.ref('stock.stock_location_output')

    def test_purchase_order_line_qty_available_real(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'sale_stock'),
        ])
        if module.state != 'installed':
            self.skipTest('Module %s not installed, ignore test.' % module)
        qty = 100.0
        self.env['stock.quant']._update_available_quantity(
            self.product, self.location, qty)
        self.assertEqual(self.product.qty_available, qty)
        qty_sale = 30
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': qty_sale,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.picking_ids[0].state, 'assigned')
        qty_purchase = 10
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'product_qty': qty_purchase,
                'date_planned': fields.Datetime.today(),
                'product_uom': self.product.uom_id.id,
                'price_unit': self.product.standard_price})]
        })
        self.product._compute_quantities()
        self.assertEqual(
            purchase.order_line[0].qty_available_real, qty - qty_sale)
