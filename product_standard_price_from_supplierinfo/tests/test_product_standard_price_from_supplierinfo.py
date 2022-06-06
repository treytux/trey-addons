###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductStandardPriceFromSupplierinfo(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Supplier Partner #1',
            'supplier': True,
        })
        self.template = self.env['product.template'].create({
            'name': 'Test Purchase Product',
            'purchase_method': 'purchase',
            'type': 'product',
            'standard_price': 10.00,
        })

    def test_standard_price(self):
        product = self.template.product_variant_ids
        self.supplierinfo_1 = self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 100.00,
            'discount': 10.00,
            'sequence': 10
        })
        self.assertEquals(self.template.standard_price, 90.00)
        self.assertEquals(product.standard_price, 90.00)
        self.supplierinfo_1.sequence = 20
        self.supplierinfo_2 = self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 1000.00,
            'discount': 10.00,
            'sequence': 10
        })
        self.assertEquals(self.template.standard_price, 900.00)
        self.assertEquals(product.standard_price, 900.00)

    def test_standard_price_new(self):
        product = self.template.product_variant_ids
        info = self.env['product.supplierinfo'].new({
            'name': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 100.00,
            'discount': 10.00,
            'sequence': 10
        })
        info = info.create(info._convert_to_write(info._cache))
        self.assertEquals(self.template.standard_price, 90.00)
        self.assertEquals(product.standard_price, 90.00)

    def test_suppplierinfo_price_0(self):
        product = self.template.product_variant_ids
        self.supplierinfo = self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 0.00,
            'sequence': 10
        })
        self.assertEquals(self.template.standard_price, 0.00)
        self.assertEquals(product.standard_price, 0.00)

    def test_product_variant(self):
        attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        template = self.env['product.template'].create({
            'name': 'Test Purchase Product',
            'purchase_method': 'purchase',
            'type': 'product',
            'standard_price': 10.00,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEquals(len(template.product_variant_ids), 3)
        line1 = self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': template.id,
            'price': 100.00,
            'sequence': 10,
        })
        line2 = self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': template.id,
            'price': 200.00,
            'sequence': 20,
        })
        self.assertEquals(template.standard_price, 0.00)
        self.assertEquals(
            template.product_variant_ids.mapped('standard_price'),
            [100.00, 100.00, 100.00])
        line1.sequence = 30
        self.assertEquals(
            template.product_variant_ids.mapped('standard_price'),
            [200.00, 200.00, 200.00])
        line2.sequence = 40
        self.assertEquals(
            template.product_variant_ids.mapped('standard_price'),
            [100.00, 100.00, 100.00])
        line2.sequence = 20
        self.assertEquals(
            template.product_variant_ids.mapped('standard_price'),
            [200.00, 200.00, 200.00])
        line1.sequence = 10
        self.assertEquals(
            template.product_variant_ids.mapped('standard_price'),
            [100.00, 100.00, 100.00])
        self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_id': template.product_variant_ids[0].id,
            'product_tmpl_id': template.id,
            'price': 300.00,
            'sequence': 90
        })
        self.assertEquals(
            template.product_variant_ids.mapped('standard_price'),
            [300.00, 100.00, 100.00])

    def test_product_variant_supplierinfo_first(self):
        attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        template = self.env['product.template'].create({
            'name': 'Test Purchase Product',
            'purchase_method': 'purchase',
            'type': 'product',
            'standard_price': 10.00,
        })
        self.assertEquals(len(template.product_variant_ids), 1)
        line1 = self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': template.id,
            'price': 100.00,
            'sequence': 10,
        })
        line2 = self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': template.id,
            'price': 200.00,
            'sequence': 20,
        })
        template.write({
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEquals(len(template.product_variant_ids), 3)
        self.assertEquals(template.standard_price, 0.00)
        self.assertEquals(
            template.product_variant_ids.mapped('standard_price'),
            [100.00, 100.00, 100.00])
        line1.sequence = 30
        self.assertEquals(
            template.product_variant_ids.mapped('standard_price'),
            [200.00, 200.00, 200.00])
        line2.sequence = 40
        self.assertEquals(
            template.product_variant_ids.mapped('standard_price'),
            [100.00, 100.00, 100.00])
        line2.sequence = 20
        self.assertEquals(
            template.product_variant_ids.mapped('standard_price'),
            [200.00, 200.00, 200.00])
        line1.sequence = 10
        self.assertEquals(
            template.product_variant_ids.mapped('standard_price'),
            [100.00, 100.00, 100.00])
        self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_id': template.product_variant_ids[0].id,
            'product_tmpl_id': template.id,
            'price': 300.00,
            'sequence': 90
        })
        self.assertEquals(
            template.product_variant_ids.mapped('standard_price'),
            [300.00, 100.00, 100.00])
