###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductInactiveMrpBom(TransactionCase):
    def setUp(self):
        super().setUp()
        attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        self.product_tmpl_1 = self.env['product.template'].create({
            'name': 'Test product template',
            'type': 'product',
            'standard_price': 10.00,
        })
        self.product_tmpl_2 = self.env['product.template'].create({
            'name': 'Test product template',
            'type': 'product',
            'standard_price': 10.00,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ],
        })
        self.material_1 = self.env['product.product'].create({
            'name': 'Material_1',
            'type': 'product',
        })
        self.material_2 = self.env['product.product'].create({
            'name': 'Material_2',
            'type': 'product',
        })
        self.bom_1 = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tmpl_1.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.material_1.id,
                    'product_qty': 1,
                    'product_uom_id': self.material_1.uom_id.id,
                }),
            ]
        })
        self.bom_2 = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tmpl_2.id,
            'product_id': self.product_tmpl_2.product_variant_ids[0].id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.material_1.id,
                    'product_qty': 1,
                    'product_uom_id': self.material_1.uom_id.id,
                }),
            ]
        })
        self.bom_3 = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tmpl_2.id,
            'product_id': self.product_tmpl_2.product_variant_ids[1].id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.material_2.id,
                    'product_qty': 1,
                    'product_uom_id': self.material_2.uom_id.id,
                }),
            ]
        })
        self.bom_4 = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tmpl_2.id,
            'product_id': self.product_tmpl_2.product_variant_ids[2].id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.material_2.id,
                    'product_qty': 1,
                    'product_uom_id': self.material_2.uom_id.id,
                }),
            ]
        })
        self.bom_5 = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tmpl_2.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.material_2.id,
                    'product_qty': 1,
                    'product_uom_id': self.material_2.uom_id.id,
                }),
            ]
        })

    def test_inactive_boms_with_product_tmpl_without_variants(self):
        self.assertTrue(self.product_tmpl_1.active)
        self.assertEquals(len(self.product_tmpl_1.product_variant_ids), 1)
        self.assertEquals(self.product_tmpl_1.bom_count, 1)
        boms = self.product_tmpl_1.bom_ids
        for bom in boms:
            self.assertTrue(bom.active)
        self.product_tmpl_1.active = False
        self.assertFalse(self.product_tmpl_1.active)
        self.assertEquals(len(self.product_tmpl_1.product_variant_ids), 0)
        self.assertEquals(self.product_tmpl_1.bom_count, 0)

    def test_inactive_boms_with_product_tmpl_with_variants(self):
        self.assertTrue(self.product_tmpl_2.active)
        self.assertEquals(len(self.product_tmpl_2.product_variant_ids), 3)
        self.assertEquals(self.product_tmpl_2.bom_count, 4)
        boms = self.product_tmpl_2.bom_ids
        for bom in boms:
            self.assertTrue(bom.active)
        self.product_tmpl_2.active = False
        self.assertFalse(self.product_tmpl_2.active)
        self.assertEquals(len(self.product_tmpl_2.product_variant_ids), 0)
        self.assertEquals(self.product_tmpl_2.bom_count, 0)

    def test_inactive_boms_with_product_variant(self):
        self.assertTrue(self.product_tmpl_2.active)
        self.assertEquals(len(self.product_tmpl_2.product_variant_ids), 3)
        self.assertEquals(self.product_tmpl_2.bom_count, 4)
        product_variant_1 = self.product_tmpl_2.product_variant_ids[0]
        self.assertTrue(product_variant_1.active)
        self.assertTrue(product_variant_1.product_tmpl_id.active)
        boms = self.env['mrp.bom'].search([
            ('product_id', '=', product_variant_1.id),
        ])
        for bom in boms:
            self.assertTrue(bom.active)
        self.assertEquals(product_variant_1.bom_count, 2)
        product_variant_1.active = False
        self.assertEquals(product_variant_1.bom_count, 1)
        self.assertFalse(product_variant_1.active)
        self.assertTrue(product_variant_1.product_tmpl_id.active)
        self.assertEquals(len(self.product_tmpl_2.product_variant_ids), 2)
        for bom in boms:
            self.assertFalse(bom.active)
        product_variant_2 = self.product_tmpl_2.product_variant_ids[0]
        boms = self.env['mrp.bom'].search([
            ('product_id', '=', product_variant_2.id),
        ])
        for bom in boms:
            self.assertTrue(bom.active)
        self.assertEquals(product_variant_2.bom_count, 2)
        product_variant_2.active = False
        self.assertEquals(product_variant_2.bom_count, 1)
        self.assertFalse(product_variant_2.active)
        self.assertTrue(product_variant_2.product_tmpl_id.active)
        self.assertEquals(len(self.product_tmpl_2.product_variant_ids), 1)
        product_variant_3 = self.product_tmpl_2.product_variant_ids[0]
        boms = self.env['mrp.bom'].search([
            ('product_id', '=', product_variant_3.id),
        ])
        for bom in boms:
            self.assertTrue(bom.active)
        self.assertEquals(product_variant_3.bom_count, 2)
        product_variant_3.active = False
        self.assertEquals(product_variant_3.bom_count, 0)
        self.assertFalse(product_variant_3.active)
        self.assertFalse(product_variant_3.product_tmpl_id.active)
        self.assertEquals(len(self.product_tmpl_2.product_variant_ids), 0)

    def test_inactive_boms_with_product_without_variants(self):
        self.assertTrue(self.product_tmpl_1.active)
        self.assertEquals(len(self.product_tmpl_1.product_variant_ids), 1)
        self.assertEquals(self.product_tmpl_1.bom_count, 1)
        product_variant_1 = self.product_tmpl_1.product_variant_ids[0]
        self.assertTrue(product_variant_1.active)
        self.assertTrue(product_variant_1.product_tmpl_id.active)
        boms = self.env['mrp.bom'].search([
            ('product_id', '=', product_variant_1.id),
        ])
        for bom in boms:
            self.assertTrue(bom.active)
        self.assertEquals(product_variant_1.bom_count, 1)
        product_variant_1.active = False
        self.assertEquals(product_variant_1.bom_count, 0)
        self.assertFalse(product_variant_1.active)
        self.assertFalse(product_variant_1.product_tmpl_id.active)
        self.assertEquals(len(self.product_tmpl_1.product_variant_ids), 0)

    def test_check_message(self):
        product_variant_1 = self.product_tmpl_2.product_variant_ids[0]
        boms = self.env['mrp.bom'].search([
            ('product_id', '=', product_variant_1.id),
        ])
        self.assertEquals(len(boms.mapped('message_ids')), 1)
        product_variant_1.active = False
        self.assertEquals(len(boms.mapped('message_ids')), 2)
        for bom in boms:
            self.assertEquals(len(bom.message_ids), 2)
            self.assertTrue(bom.message_ids)
            msg = bom.message_ids[0].body
            self.assertIn('Bill of materials automatically ', msg)
