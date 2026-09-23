###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestMrpProductionLotUniqueProductVariant(TransactionCase):
    def test_unique_production_lot_in_variant(self):
        attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        product_template_1 = self.env['product.template'].create({
            'name': 'Test product template 1',
            'type': 'product',
            'standard_price': 10.00,
            'tracking': 'serial',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ],
        })
        product_1 = product_template_1.product_variant_ids[0]
        product_2 = product_template_1.product_variant_ids[1]
        product_3 = product_template_1.product_variant_ids[2]
        lot_1 = self.env['stock.production.lot'].create({
            'name': '000001',
            'product_id': product_1.id,
        })
        self.assertTrue(lot_1)
        self.assertEquals(lot_1.name, '000001')
        with self.assertRaises(ValidationError) as result:
            self.env['stock.production.lot'].create({
                'name': '000001',
                'product_id': product_2.id,
            })
        self.assertEquals(
            'The serial number "000001" is already in use in another variant '
            'of this product.',
            result.exception.name)
        lot_2 = self.env['stock.production.lot'].create({
            'name': '000002',
            'product_id': product_2.id,
        })
        self.assertTrue(lot_2)
        self.assertEquals(lot_2.name, '000002')
        company_2 = self.env['res.company'].browse(2)
        product_3.company_id = company_2
        with self.assertRaises(ValidationError) as result:
            self.env['stock.production.lot'].create({
                'name': '000001',
                'product_id': product_3.id,
            })
        self.assertEquals(
            'The serial number "000001" is already in use in another '
            'variant of this product.',
            result.exception.name)
        lot_3 = self.env['stock.production.lot'].create({
            'name': '000003',
            'product_id': product_3.id,
        })
        self.assertTrue(lot_3)
        self.assertEquals(lot_3.name, '000003')
        product_template_2 = self.env['product.template'].create({
            'name': 'Test product template 2',
            'type': 'product',
            'standard_price': 10.00,
            'tracking': 'serial',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ],
        })
        product_4 = product_template_2.product_variant_ids[0]
        product_5 = product_template_2.product_variant_ids[1]
        product_5.company_id = company_2
        lot_4 = self.env['stock.production.lot'].create({
            'name': '000001',
            'product_id': product_4.id,
        })
        self.assertTrue(lot_4)
        self.assertEquals(lot_4.name, '000001')
        with self.assertRaises(ValidationError) as result:
            self.env['stock.production.lot'].create({
                'name': '000001',
                'product_id': product_5.id,
            })
        self.assertEquals(
            'The serial number "000001" is already in use in another '
            'variant of this product.',
            result.exception.name)
        lot_5 = self.env['stock.production.lot'].create({
            'name': '000005',
            'product_id': product_5.id,
        })
        self.assertTrue(lot_5)
        self.assertEquals(lot_5.name, '000005')
