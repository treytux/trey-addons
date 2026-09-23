###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestMrpProductionDefaultLocation(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.table = self.env['product.product'].create({
            'name': 'Test Table',
            'type': 'product',
        })
        self.board = self.env['product.product'].create({
            'name': 'Test Board',
            'type': 'product',
        })
        self.leg = self.env['product.product'].create({
            'name': 'Test Leg',
            'type': 'product',
        })
        self.bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.table.product_tmpl_id.id,
            'product_id': self.table.id,
            'product_uom_id': self.table.uom_id.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.board.id,
                    'product_qty': 1,
                    'product_uom_id': self.board.uom_id.id,
                }),
                (0, 0, {
                    'product_id': self.leg.id,
                    'product_qty': 4,
                    'product_uom_id': self.leg.uom_id.id,
                }),
            ],
        })

    def test_default_company_empty(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'product_qty': 1,
            'product_uom_id': self.table.uom_id.id,
            'bom_id': self.bom.id,
        })
        self.assertEqual(mrp.location_src_id, self.stock_location)
        self.assertEqual(mrp.location_dest_id, self.stock_location)

    def test_default_company_fill(self):
        location_01 = self.env['stock.location'].create({
            'name': 'Location 01',
            'usage': 'internal',
        })
        location_02 = self.env['stock.location'].create({
            'name': 'Location 02',
            'usage': 'internal',
        })
        self.env.company.mrp_location_src_id = location_01
        self.env.company.mrp_location_dst_id = location_02
        mrp = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'product_qty': 1,
            'product_uom_id': self.table.uom_id.id,
            'bom_id': self.bom.id,
        })
        self.assertEqual(mrp.location_src_id, location_01)
        self.assertEqual(mrp.location_dest_id, location_02)
        mrp_found = self.env['mrp.production'].search([
            ('location_src_id', '=', location_01.id),
        ])
        self.assertEqual(mrp_found, mrp)
        mrp_found = self.env['mrp.production'].search([
            ('location_dest_id', '=', location_02.id),
        ])
        self.assertEqual(mrp_found, mrp)
