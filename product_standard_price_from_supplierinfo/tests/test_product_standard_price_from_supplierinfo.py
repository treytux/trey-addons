###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductStandardPriceFromSupplierinfo(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Supplier Partner #1',
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
            'partner_id': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 100.00,
            'discount': 10.00,
            'sequence': 10,
        })
        self.assertEqual(self.template.standard_price, 90.00)
        self.assertEqual(product.standard_price, 90.00)
        self.supplierinfo_1.sequence = 20
        self.supplierinfo_2 = self.env['product.supplierinfo'].create({
            'partner_id': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 1000.00,
            'discount': 10.00,
            'sequence': 10,
        })
        self.assertEqual(self.template.standard_price, 900.00)
        self.assertEqual(product.standard_price, 900.00)

    def test_standard_price_new(self):
        product = self.template.product_variant_ids
        info = self.env['product.supplierinfo'].new({
            'partner_id': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 100.00,
            'discount': 10.00,
            'sequence': 10,
        })
        info = info.create(info._convert_to_write(info._cache))
        self.assertEqual(self.template.standard_price, 90.00)
        self.assertEqual(product.standard_price, 90.00)

    def test_standard_price_discount_update(self):
        product = self.template.product_variant_ids
        supplierinfo = self.env['product.supplierinfo'].create({
            'partner_id': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 100.00,
            'discount': 10.00,
            'sequence': 10,
        })
        self.assertEqual(product.standard_price, 90.00)
        supplierinfo.discount = 20.00
        self.assertEqual(self.template.standard_price, 80.00)
        self.assertEqual(product.standard_price, 80.00)

    def test_standard_price_price_update(self):
        product = self.template.product_variant_ids
        supplierinfo = self.env['product.supplierinfo'].create({
            'partner_id': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 100.00,
            'discount': 10.00,
            'sequence': 10,
        })
        supplierinfo.price = 200.00

        self.assertEqual(self.template.standard_price, 180.00)
        self.assertEqual(product.standard_price, 180.00)

    def test_standard_price_discount_100(self):
        product = self.template.product_variant_ids
        supplierinfo = self.env['product.supplierinfo'].create({
            'partner_id': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 100.00,
            'discount': 100.00,
            'sequence': 10,
        })
        self.assertEqual(supplierinfo.price_get(), 0.00)
        self.assertEqual(self.template.standard_price, 0.00)
        self.assertEqual(product.standard_price, 0.00)

    def test_create_supplierinfo_multi(self):
        product = self.template.product_variant_ids
        self.env['product.supplierinfo'].create([
            {
                'partner_id': self.partner.id,
                'product_tmpl_id': self.template.id,
                'price': 100.00,
                'sequence': 10,
            },
            {
                'partner_id': self.partner.id,
                'product_tmpl_id': self.template.id,
                'price': 200.00,
                'sequence': 20,
            },
        ])
        self.assertEqual(self.template.standard_price, 100.00)
        self.assertEqual(product.standard_price, 100.00)

    def test_supplierinfo_price_0(self):
        product = self.template.product_variant_ids
        self.supplierinfo = self.env['product.supplierinfo'].create({
            'partner_id': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 0.00,
            'sequence': 10,
        })
        self.assertEqual(self.template.standard_price, 0.00)
        self.assertEqual(product.standard_price, 0.00)

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
        self.assertEqual(len(template.product_variant_ids), 3)
        supplierinfo1 = self.env['product.supplierinfo'].create({
            'partner_id': self.partner.id,
            'product_tmpl_id': template.id,
            'price': 100.00,
            'sequence': 10,
        })
        supplierinfo2 = self.env['product.supplierinfo'].create({
            'partner_id': self.partner.id,
            'product_tmpl_id': template.id,
            'price': 200.00,
            'sequence': 20,
        })
        self.assertEqual(template.standard_price, 0.00)
        self.assertEqual(
            template.product_variant_ids.mapped('standard_price'),
            [100.00, 100.00, 100.00])
        supplierinfo1.sequence = 30
        self.assertEqual(
            template.product_variant_ids.mapped('standard_price'),
            [200.00, 200.00, 200.00])
        supplierinfo2.sequence = 40
        self.assertEqual(
            template.product_variant_ids.mapped('standard_price'),
            [100.00, 100.00, 100.00])
        supplierinfo2.sequence = 20
        self.assertEqual(
            template.product_variant_ids.mapped('standard_price'),
            [200.00, 200.00, 200.00])
        supplierinfo1.sequence = 10
        self.assertEqual(
            template.product_variant_ids.mapped('standard_price'),
            [100.00, 100.00, 100.00])
        self.env['product.supplierinfo'].create({
            'partner_id': self.partner.id,
            'product_id': template.product_variant_ids[0].id,
            'product_tmpl_id': template.id,
            'price': 300.00,
            'sequence': 90,
        })
        self.assertEqual(
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
        self.assertEqual(len(template.product_variant_ids), 1)
        supplierinfo1 = self.env['product.supplierinfo'].create({
            'partner_id': self.partner.id,
            'product_tmpl_id': template.id,
            'price': 100.00,
            'sequence': 10,
        })
        supplierinfo2 = self.env['product.supplierinfo'].create({
            'partner_id': self.partner.id,
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
        self.assertEqual(len(template.product_variant_ids), 3)
        self.assertEqual(template.standard_price, 0.00)
        self.assertEqual(
            template.product_variant_ids.mapped('standard_price'),
            [100.00, 100.00, 100.00])
        supplierinfo1.sequence = 30
        self.assertEqual(
            template.product_variant_ids.mapped('standard_price'),
            [200.00, 200.00, 200.00])
        supplierinfo2.sequence = 40
        self.assertEqual(
            template.product_variant_ids.mapped('standard_price'),
            [100.00, 100.00, 100.00])
        supplierinfo2.sequence = 20
        self.assertEqual(
            template.product_variant_ids.mapped('standard_price'),
            [200.00, 200.00, 200.00])
        supplierinfo1.sequence = 10
        self.assertEqual(
            template.product_variant_ids.mapped('standard_price'),
            [100.00, 100.00, 100.00])
        self.env['product.supplierinfo'].create({
            'partner_id': self.partner.id,
            'product_id': template.product_variant_ids[0].id,
            'product_tmpl_id': template.id,
            'price': 300.00,
            'sequence': 90,
        })
        self.assertEqual(
            template.product_variant_ids.mapped('standard_price'),
            [300.00, 100.00, 100.00])
