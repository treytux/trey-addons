###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductSupplierPrice(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Supplier Partner #1',
            'supplier': True,
        })
        self.template = self.env['product.template'].create({
            'name': 'Test Purchase Product',
            'type': 'consu',
            'standard_price': 10.00,
        })

    def test_supplier_price(self):
        product = self.template.product_variant_ids
        self.assertEqual(self.template.supplier_cost, 0.00)
        self.assertEqual(product.supplier_cost, 0.00)
        info_1 = self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 100.00,
            'sequence': 10,
        })
        self.assertEqual(self.template.supplier_cost, 100.00)
        self.assertEqual(product.supplier_cost, 100.00)
        info_1.sequence = 20
        self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 1000.00,
            'sequence': 10,
        })
        self.assertEqual(self.template.supplier_cost, 1000.00)
        self.assertEqual(product.supplier_cost, 1000.00)

    def test_supplier_price_new(self):
        product = self.template.product_variant_ids
        info = self.env['product.supplierinfo'].new({
            'name': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 100.00,
            'sequence': 10,
        })
        info = info.create(info._convert_to_write(info._cache))
        self.assertEqual(self.template.supplier_cost, 100.00)
        self.assertEqual(product.supplier_cost, 100.00)

    def test_suppplierinfo_price_0(self):
        product = self.template.product_variant_ids
        self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 0.00,
            'sequence': 10,
        })
        self.assertEqual(self.template.supplier_cost, 0.00)
        self.assertEqual(product.supplier_cost, 0.00)

    def test_create_product_first(self):
        product = self.env['product.product'].create({
            'name': 'Test Purchase Product',
            'type': 'consu',
            'standard_price': 10.00,
        })
        self.assertEqual(len(product.product_tmpl_id.product_variant_ids), 1)
        self.assertEqual(product.product_tmpl_id.supplier_cost, 0.00)
        self.assertEqual(product.supplier_cost, 0.00)
        info_1 = self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'price': 100.00,
            'sequence': 10,
        })
        info_2 = self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'price': 200.00,
            'sequence': 20,
        })
        self.assertEqual(product.product_tmpl_id.supplier_cost, 100.00)
        self.assertEqual(product.supplier_cost, 100.00)
        info_1.sequence = 30
        self.assertEqual(info_1.sequence, 30)
        self.assertEqual(info_2.sequence, 20)
        self.assertEqual(product.product_tmpl_id.supplier_cost, 200.00)
        self.assertEqual(product.supplier_cost, 200.00)
        info_2.sequence = 40
        self.assertEqual(product.product_tmpl_id.supplier_cost, 100.00)
        self.assertEqual(product.supplier_cost, 100.00)

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
            'type': 'consu',
            'standard_price': 10.00,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEqual(self.template.supplier_cost, 0.00)
        self.assertEqual(
            template.product_variant_ids.mapped('supplier_cost'),
            [0.00, 0.00, 0.00])
        self.assertEqual(len(template.product_variant_ids), 3)
        info_1 = self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': template.id,
            'price': 100.00,
            'sequence': 10,
        })
        info_2 = self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': template.id,
            'price': 200.00,
            'sequence': 20,
        })
        self.assertEqual(template.supplier_cost, 0.00)
        self.assertEqual(
            template.product_variant_ids.mapped('supplier_cost'),
            [100.00, 100.00, 100.00])
        info_1.sequence = 30
        self.assertEqual(
            template.product_variant_ids.mapped('supplier_cost'),
            [200.00, 200.00, 200.00])
        info_2.sequence = 40
        self.assertEqual(
            template.product_variant_ids.mapped('supplier_cost'),
            [100.00, 100.00, 100.00])
        info_2.sequence = 20
        self.assertEqual(
            template.product_variant_ids.mapped('supplier_cost'),
            [200.00, 200.00, 200.00])
        info_1.sequence = 10
        self.assertEqual(
            template.product_variant_ids.mapped('supplier_cost'),
            [100.00, 100.00, 100.00])
        info_1.sequence = 30
        self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_id': template.product_variant_ids[0].id,
            'product_tmpl_id': template.id,
            'price': 300.00,
            'sequence': 10,
        })
        self.assertEqual(
            template.product_variant_ids.mapped('supplier_cost'),
            [300.00, 200.00, 200.00])

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
            'type': 'consu',
        })
        self.assertEqual(len(template.product_variant_ids), 1)
        info_1 = self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': template.id,
            'price': 100.00,
            'sequence': 10,
        })
        info_2 = self.env['product.supplierinfo'].create({
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
        self.assertEqual(len(template.product_variant_ids), 3)
        self.assertEqual(template.supplier_cost, 0.00)
        self.assertEqual(
            template.product_variant_ids.mapped('supplier_cost'),
            [100.00, 100.00, 100.00])
        info_1.sequence = 30
        self.assertEqual(
            template.product_variant_ids.mapped('supplier_cost'),
            [200.00, 200.00, 200.00])
        info_2.sequence = 40
        self.assertEqual(
            template.product_variant_ids.mapped('supplier_cost'),
            [100.00, 100.00, 100.00])
        info_2.sequence = 20
        self.assertEqual(
            template.product_variant_ids.mapped('supplier_cost'),
            [200.00, 200.00, 200.00])
        info_1.sequence = 10
        self.assertEqual(
            template.product_variant_ids.mapped('supplier_cost'),
            [100.00, 100.00, 100.00])
        self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_id': template.product_variant_ids[0].id,
            'product_tmpl_id': template.id,
            'price': 300.00,
            'sequence': 5,
        })
        self.assertEqual(
            template.product_variant_ids.mapped('supplier_cost'),
            [300.00, 100.00, 100.00])

    def test_supplier_price_in_pricelist_item(self):
        product = self.template.product_variant_ids
        self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_tmpl_id': self.template.id,
            'price': 50.00,
            'sequence': 10,
        })
        self.assertEqual(self.template.supplier_cost, 50.00)
        self.assertEqual(product.supplier_cost, 50.00)
        pricelist = self.env['product.pricelist'].create({
            'name': 'Test pricelist',
            'item_ids': [
                (0, 0, {
                    'applied_on': '1_product',
                    'product_id': product.id,
                    'compute_price': 'formula',
                    'base': 'list_price',
                }),
            ],
        })
        pricelist = pricelist.with_context(
            lang=self.partner.lang,
            partner=self.partner,
            quantity=1,
            pricelist=pricelist.id,
        )
        product.list_price = 100
        price, rule = pricelist.get_product_price_rule(
            product, 1.0, self.partner)
        self.assertEquals(price, 100)
        pricelist.item_ids[0].base = 'supplier_cost'
        price, rule = pricelist.get_product_price_rule(
            product, 1.0, self.partner)
        self.assertEquals(price, 50.00)
