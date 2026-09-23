###############################################################################
# For copyright and license notices, see __manifest__.py file
###############################################################################
from odoo.tests.common import TransactionCase


class TestWebsiteSaleStockPickingControl(TransactionCase):

    def setUp(self):
        super().setUp()
        self.website = self.env.ref('website.default_website')
        self.partner = self.env['res.partner'].create({
            'name': 'Website stock picking test partner',
        })
        product_template = self.env['product.template'].create({
            'name': 'Website stock picking test product',
            'type': 'product',
            'list_price': 10.0,
        })
        self.product = product_template.product_variant_id

    def _create_sale_order(self):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'website_id': self.website.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.display_name,
                'product_uom_qty': 1.0,
                'product_uom': self.product.uom_id.id,
                'price_unit': self.product.list_price,
            })],
        })

    def test_website_order_skips_delivery_order(self):
        self.website.sale_order_skip_stock_picking = True
        sale = self._create_sale_order()
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertFalse(sale.picking_ids)
        self.assertFalse(sale.procurement_group_id)
        self.assertFalse(sale.order_line.mapped('move_ids'))

    def test_website_order_keeps_standard_delivery_order(self):
        self.website.sale_order_skip_stock_picking = False
        sale = self._create_sale_order()
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertTrue(sale.picking_ids)
        self.assertTrue(sale.order_line.mapped('move_ids'))
