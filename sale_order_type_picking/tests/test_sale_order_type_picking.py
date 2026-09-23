###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests import common


class TestSaleOrderTypePicking(common.TransactionCase):

    def setUp(self):
        super().setUpClass()
        self.company = self.env.company
        self.partner = self.env['res.partner'].create({
            'name': 'Test customer',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test product',
            'type': 'product',
            'sale_ok': True,
            'list_price': 10,
        })
        self.sale_type = self.env['sale.order.type'].create({
            'name': 'Test sale type',
            'company_id': self.company.id,
        })
        self.other_sale_type = self.env['sale.order.type'].create({
            'name': 'Other test sale type',
            'company_id': self.company.id,
        })

    def create_sale_order(self, sale_type):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'type_id': sale_type.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 10,
            })],
        })

    def test_sale_type_propagated_to_picking(self):
        sale = self.create_sale_order(self.sale_type)
        sale.action_confirm()
        self.assertTrue(sale.picking_ids)
        self.assertEqual(
            sale.picking_ids.mapped('sale_type_id'), self.sale_type)

    def test_sale_type_changes_in_stored_field(self):
        sale = self.create_sale_order(self.sale_type)
        sale.action_confirm()
        picking = sale.picking_ids
        sale.type_id = self.other_sale_type
        self.assertEqual(picking.sale_type_id, self.other_sale_type)

    def test_picking_without_sale_order_no_sale_type(self):
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.env.ref(
                'stock.stock_location_stock').id,
            'scheduled_date': fields.Datetime.now(),
        })
        self.assertFalse(picking.sale_id)
        self.assertFalse(picking.sale_type_id)
