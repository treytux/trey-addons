###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import hashlib
import secrets

from lxml import etree
from odoo.tests.common import TransactionCase

BM_NS = 'http://www.bmecat.org/bmecat/2005'


class TestBmcatExport(TransactionCase):

    def _generate_token(self):
        raw = secrets.token_bytes(32)
        return hashlib.sha256(raw).hexdigest()[:40]

    def setUp(self):
        super().setUp()
        self.Catalog = self.env['product.catalog']
        self.Product = self.env['product.template']
        self.ProductProduct = self.env['product.product']
        self.Quant = self.env['stock.quant']
        self.category = self.env['product.category'].create(
            {'name': 'Test Category'})
        self.catalog = self.Catalog.create({
            'name': 'Test BMEcat',
            'bmcat_token': self._generate_token(),
            'bmcat_cache_hours': 2,
        })

    def _create_product(self, **kwargs):
        vals = {
            'name': 'Test Product',
            'default_code': 'TST-001',
            'barcode': '1234567890123',
            'list_price': 25.50,
            'weight': 1.5,
            'type': 'product',
            'categ_id': self.category.id,
            'catalog_ids': [(4, self.catalog.id)],
        }
        vals.update(kwargs)
        product = self.Product.create(vals)
        variant = self.ProductProduct.search([
            ('product_tmpl_id', '=', product.id),
        ], limit=1)
        if not variant:
            self.ProductProduct.create({
                'product_tmpl_id': product.id,
                'default_code': product.default_code,
            })
        return product

    def _set_stock(self, product, qty, location=None):
        variant = self.ProductProduct.search([
            ('product_tmpl_id', '=', product.id),
        ], limit=1)
        location = location or self.env.ref('stock.stock_location_stock')
        quant = self.Quant.create({
            'product_id': variant.id,
            'location_id': location.id,
            'quantity': qty,
        })
        return quant

    def _get_stock_text(self, xml_bytes):
        root = etree.fromstring(xml_bytes)
        ns = {'bm': BM_NS}
        article = root.find('.//bm:ARTICLE_STOCK/bm:STOCK', ns)
        return article.text if article is not None else None

    def test_generate_token(self):
        self.assertTrue(self.catalog.bmcat_token)
        self.assertEqual(len(self.catalog.bmcat_token), 40)

    def test_token_unique_constraint(self):
        import psycopg2
        with self.assertRaises(psycopg2.errors.UniqueViolation):
            self.env.cr.execute(
                'INSERT INTO product_catalog (name, bmcat_token) '
                'VALUES (%s, %s)',
                ['Duplicate token', self.catalog.bmcat_token])

    def test_generate_xml_empty_catalog(self):
        products = self.Product
        xml_bytes = self.catalog._bmcat_generate_xml(products)
        self.assertTrue(xml_bytes)
        xml_str = xml_bytes.decode('utf-8')
        self.assertIn('<?xml', xml_str)
        self.assertNotIn('ARTICLE', xml_str)

    def test_generate_xml_with_products(self):
        self._create_product()
        products = self.Product.search([
            ('catalog_ids', 'in', self.catalog.id),
        ])
        self.assertEqual(len(products), 1)
        xml_bytes = self.catalog._bmcat_generate_xml(products)
        self.assertTrue(xml_bytes)
        xml_str = xml_bytes.decode('utf-8')
        self.assertIn('<?xml', xml_str)
        self.assertIn('BMECAT', xml_str)
        self.assertIn('TST-001', xml_str)
        self.assertIn('Test Product', xml_str)
        self.assertIn('25.50', xml_str)
        self.assertIn('1.5', xml_str)
        self.assertIn('Test Category', xml_str)

    def test_cache_valid_no_cache_hours(self):
        self.catalog.bmcat_cache_hours = 0
        self.assertFalse(self.catalog._bmcat_cache_valid())

    def test_cache_valid_no_file(self):
        self.catalog.bmcat_cache_hours = 2
        self.assertFalse(self.catalog._bmcat_cache_valid())

    def test_cache_valid_within_window(self):
        self._create_product(default_code='CACHE-001')
        products = self.Product.search([
            ('catalog_ids', 'in', self.catalog.id),
        ])
        xml_bytes = self.catalog._bmcat_generate_xml(products)
        self.catalog._bmcat_store_file(xml_bytes)
        self.assertTrue(self.catalog._bmcat_cache_valid())

    def test_regenerate_token(self):
        old_token = self.catalog.bmcat_token
        self.catalog.action_bmcat_regenerate_token()
        self.assertNotEqual(self.catalog.bmcat_token, old_token)
        self.assertTrue(self.catalog.bmcat_token)

    def test_store_file(self):
        content = b'<test>data</test>'
        self.catalog._bmcat_store_file(content)
        self.assertTrue(self.catalog.bmcat_file)
        self.assertEqual(self.catalog.bmcat_file_size, len(content))
        self.assertTrue(self.catalog.bmcat_generated_at)

    def test_stock_mode_none(self):
        self.catalog.bmcat_stock_mode = 'none'
        product = self._create_product()
        self._set_stock(product, 50.0)
        products = self.Product.search([
            ('catalog_ids', 'in', self.catalog.id),
        ])
        xml_bytes = self.catalog._bmcat_generate_xml(products)
        stock_text = self._get_stock_text(xml_bytes)
        self.assertIsNone(stock_text)

    def test_stock_mode_real(self):
        self.catalog.bmcat_stock_mode = 'real'
        product = self._create_product()
        self._set_stock(product, 25.0)
        products = self.Product.search([
            ('catalog_ids', 'in', self.catalog.id),
        ])
        xml_bytes = self.catalog._bmcat_generate_xml(products)
        stock_text = self._get_stock_text(xml_bytes)
        self.assertEqual(stock_text, '25.0')

    def test_stock_mode_real_zero(self):
        self.catalog.bmcat_stock_mode = 'real'
        product = self._create_product()
        self._set_stock(product, 0.0)
        products = self.Product.search([
            ('catalog_ids', 'in', self.catalog.id),
        ])
        xml_bytes = self.catalog._bmcat_generate_xml(products)
        stock_text = self._get_stock_text(xml_bytes)
        self.assertEqual(stock_text, '0.0')

    def test_stock_mode_forecast(self):
        self.catalog.bmcat_stock_mode = 'forecast'
        product = self._create_product()
        self._set_stock(product, 10.0)
        products = self.Product.search([
            ('catalog_ids', 'in', self.catalog.id),
        ])
        xml_bytes = self.catalog._bmcat_generate_xml(products)
        stock_text = self._get_stock_text(xml_bytes)
        self.assertEqual(stock_text, '10.0')

    def test_stock_mode_boolean_true(self):
        self.catalog.bmcat_stock_mode = 'boolean'
        product = self._create_product()
        self._set_stock(product, 5.0)
        products = self.Product.search([
            ('catalog_ids', 'in', self.catalog.id),
        ])
        xml_bytes = self.catalog._bmcat_generate_xml(products)
        stock_text = self._get_stock_text(xml_bytes)
        self.assertEqual(stock_text, 'yes')

    def test_stock_mode_boolean_false(self):
        self.catalog.bmcat_stock_mode = 'boolean'
        product = self._create_product()
        self._set_stock(product, 0.0)
        products = self.Product.search([
            ('catalog_ids', 'in', self.catalog.id),
        ])
        xml_bytes = self.catalog._bmcat_generate_xml(products)
        stock_text = self._get_stock_text(xml_bytes)
        self.assertEqual(stock_text, 'no')

    def test_stock_with_locations(self):
        self.catalog.bmcat_stock_mode = 'real'
        loc_a = self.env['stock.location'].create({
            'name': 'Location A',
            'location_id': self.env.ref('stock.stock_location_stock').id,
        })
        loc_b = self.env['stock.location'].create({
            'name': 'Location B',
            'location_id': self.env.ref('stock.stock_location_stock').id,
        })
        self.catalog.bmcat_stock_location_ids = [(4, loc_a.id), (4, loc_b.id)]
        product = self._create_product()
        self._set_stock(product, 30.0, location=loc_a)
        self._set_stock(product, 20.0, location=loc_b)
        products = self.Product.search([
            ('catalog_ids', 'in', self.catalog.id),
        ])
        xml_bytes = self.catalog._bmcat_generate_xml(products)
        stock_text = self._get_stock_text(xml_bytes)
        self.assertEqual(stock_text, '50.0')

    def test_stock_with_locations_subset(self):
        self.catalog.bmcat_stock_mode = 'real'
        warehouse = self.env.ref('stock.warehouse0')
        loc_a = self.env['stock.location'].create({
            'name': 'Location A',
            'location_id': warehouse.lot_stock_id.id,
        })
        loc_b = self.env['stock.location'].create({
            'name': 'Location B',
            'location_id': warehouse.lot_stock_id.id,
        })
        self.catalog.bmcat_stock_location_ids = [(4, loc_a.id)]
        product = self._create_product()
        self._set_stock(product, 15.0, location=loc_a)
        self._set_stock(product, 35.0, location=loc_b)
        products = self.Product.search([
            ('catalog_ids', 'in', self.catalog.id),
        ])
        xml_bytes = self.catalog._bmcat_generate_xml(products)
        stock_text = self._get_stock_text(xml_bytes)
        self.assertEqual(stock_text, '15.0')

    def test_get_stock_qty_real(self):
        self.catalog.bmcat_stock_mode = 'real'
        product = self._create_product()
        self._set_stock(product, 100.0)
        qty = self.catalog._bmcat_get_stock_qty(product)
        self.assertEqual(qty, 100.0)

    def test_get_stock_qty_none(self):
        self.catalog.bmcat_stock_mode = 'none'
        product = self._create_product()
        self._set_stock(product, 100.0)
        qty = self.catalog._bmcat_get_stock_qty(product)
        self.assertIsNone(qty)
