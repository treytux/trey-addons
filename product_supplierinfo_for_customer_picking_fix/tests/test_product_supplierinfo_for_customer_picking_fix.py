###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductSupplierinfoForCustomerPickingFix(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.browse_ref("product.product_product_3")
        self.partner = self.browse_ref("base.res_partner_2")
        self.product.write({
            'customer_ids': [(0, 0, {
                'name': self.partner.id,
                'product_code': 'test_agrolait',
            })],
        })

    def test_product_supplierinfo_for_customer_picking(self):
        delivery_picking = self.env['stock.picking'].new({
            'partner_id': self.partner.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
        })
        delivery_picking.onchange_picking_type()
        delivery_picking = self.env['stock.picking'].create({
            'partner_id': delivery_picking.partner_id.id,
            'picking_type_id': delivery_picking.picking_type_id.id,
            'location_id': delivery_picking.location_id.id,
            'location_dest_id': delivery_picking.location_dest_id.id,
            'move_lines': [(0, 0, {
                'name': self.product.partner_ref,
                'product_id': self.product.id,
                'product_uom': self.product.uom_id.id,
                'product_uom_qty': 1.0,
            })]
        })
        move = delivery_picking.move_lines[0]
        move._compute_product_customer_code()
        self.assertEqual(move.product_customer_code, 'test_agrolait')
        self.assertEqual(
            move.product_tmpl_id.customer_ids[0].name,
            move.picking_id.partner_id)
