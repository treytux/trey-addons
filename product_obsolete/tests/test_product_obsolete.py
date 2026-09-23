###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductObsolete(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product 01',
            'standard_price': 10,
            'list_price': 100,
        })
        self.attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['White', 'Black']:
            self.env['product.attribute.value'].create({
                'attribute_id': self.attr.id,
                'name': value,
            })
        self.product_tmpl_02 = self.env['product.template'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product 02',
            'standard_price': 10.00,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr.id,
                    'value_ids': [(6, 0, self.attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEquals(len(self.product_tmpl_02.product_variant_ids), 2)
        self.product_02_white = (
            self.product_tmpl_02.product_variant_ids.filtered(
                lambda p: p.attribute_value_ids.name == 'White'))
        self.assertEquals(len(self.product_02_white), 1)
        self.product_02_black = (
            self.product_tmpl_02.product_variant_ids.filtered(
                lambda p: p.attribute_value_ids.name == 'Black'))
        self.assertEquals(len(self.product_02_black), 1)
        self.supplier_location = self.env.ref('stock.stock_location_suppliers')
        self.stock_location = self.env.ref('stock.stock_location_stock')

    def create_picking_in(self, product, qty):
        picking = self.env['stock.picking'].create({
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'move_lines': [
                (0, 0, {
                    'product_id': product.id,
                    'name': product.name,
                    'product_uom': product.uom_id.id,
                    'product_uom_qty': qty,
                    'procure_method': 'make_to_stock',
                }),
            ],
        })
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        return picking

    def test_product_obsolete_one_variant(self):
        self.assertFalse(self.product_01.is_obsolete)
        self.assertFalse(self.product_01.product_tmpl_id.is_obsolete)
        self.product_01.is_obsolete = True
        self.assertTrue(self.product_01.is_obsolete)
        product_tmpl_01 = self.product_01.product_tmpl_id
        self.assertTrue(product_tmpl_01.is_obsolete)
        self.product_01.is_obsolete = False
        self.assertFalse(self.product_01.is_obsolete)
        self.assertFalse(product_tmpl_01.is_obsolete)
        product_tmpl_01.is_obsolete = True
        self.assertTrue(self.product_01.is_obsolete)
        product_tmpl_01.is_obsolete = False
        self.assertFalse(self.product_01.is_obsolete)
        self.assertFalse(product_tmpl_01.is_obsolete)

    def test_product_obsolete_several_variants(self):
        self.assertFalse(self.product_02_black.is_obsolete)
        self.assertFalse(self.product_02_white.is_obsolete)
        self.assertFalse(self.product_tmpl_02.is_obsolete)
        self.product_02_black.is_obsolete = True
        self.assertTrue(self.product_02_black.is_obsolete)
        self.assertFalse(self.product_02_white.is_obsolete)
        self.assertFalse(self.product_tmpl_02.is_obsolete)
        self.product_02_white.is_obsolete = True
        self.assertTrue(self.product_02_white.is_obsolete)
        self.assertTrue(self.product_02_black.is_obsolete)
        self.assertTrue(self.product_tmpl_02.is_obsolete)
        self.product_tmpl_02.is_obsolete = False
        self.assertFalse(self.product_tmpl_02.is_obsolete)
        self.assertFalse(self.product_02_white.is_obsolete)
        self.assertFalse(self.product_02_black.is_obsolete)

    def test_stock_move_product(self):
        self.assertFalse(self.product_01.is_obsolete)
        self.assertFalse(self.product_01.product_tmpl_id.is_obsolete)
        picking_in = self.create_picking_in(self.product_01, 10)
        self.assertFalse(picking_in.move_lines.product_is_obsolete)
        self.product_01.is_obsolete = True
        self.assertTrue(self.product_01.is_obsolete)
        product_tmpl_01 = self.product_01.product_tmpl_id
        self.assertTrue(product_tmpl_01.is_obsolete)
        self.assertTrue(picking_in.move_lines.product_is_obsolete)
        self.product_01.is_obsolete = False
        self.assertFalse(self.product_01.is_obsolete)
        self.assertFalse(product_tmpl_01.is_obsolete)
        product_tmpl_01.is_obsolete = True
        self.assertTrue(self.product_01.is_obsolete)
        product_tmpl_01.is_obsolete = False
        self.assertFalse(self.product_01.is_obsolete)
        self.assertFalse(product_tmpl_01.is_obsolete)
        self.assertFalse(picking_in.move_lines.product_is_obsolete)
