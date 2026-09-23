###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import hashlib
import logging
import secrets
from datetime import timedelta

from lxml import etree
from odoo import _, exceptions, fields, models

_log = logging.getLogger(__name__)

BMEATCAT_NS = 'http://www.bmecat.org/bmecat/2005'
XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'


class ProductCatalog(models.Model):
    _inherit = 'product.catalog'

    bmcat_token = fields.Char(
        string='BMEcat Token',
        copy=False,
        readonly=True,
    )
    bmcat_url = fields.Char(
        string='Public URL',
        compute='_compute_bmcat_url',
    )
    bmcat_cache_hours = fields.Integer(
        string='Cache hours',
        default=0,
        help='Hours to cache the generated BMEcat file. 0 = no cache.',
    )
    bmcat_file = fields.Binary(
        string='BMEcat file',
        attachment=True,
        copy=False,
        readonly=True,
    )
    bmcat_filename = fields.Char(
        string='BMEcat filename',
        default='catalog.xml',
        readonly=True,
    )
    bmcat_generated_at = fields.Datetime(
        string='Generated at',
        readonly=True,
        copy=False,
    )
    bmcat_file_size = fields.Integer(
        string='File size (bytes)',
        readonly=True,
        copy=False,
    )
    bmcat_stock_mode = fields.Selection(
        selection=[
            ('none', 'None'),
            ('boolean', 'Has stock / No stock'),
            ('real', 'Real stock'),
            ('forecast', 'Forecasted stock'),
        ],
        string='Stock info',
        default='none',
        help='Stock information to include in the BMEcat export.',
    )
    bmcat_stock_location_ids = fields.Many2many(
        comodel_name='stock.location',
        string='Stock locations',
        help='If set, stock is computed only from these locations. '
             'If empty, uses all available locations.',
    )

    _sql_constraints = [
        ('bmcat_token_unique', 'UNIQUE(bmcat_token)',
         'BMEcat token must be unique per catalog.'),
    ]

    def _compute_bmcat_url(self):
        for catalog in self:
            catalog.bmcat_url = (
                f'/bmcat/{catalog.bmcat_token}/download'
                if catalog.bmcat_token else ''
            )

    def _bmcat_safe_text(self, text):
        if not text:
            return ''
        text = str(text).replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text

    def _bmcat_generate_token(self):
        raw = secrets.token_bytes(32)
        return hashlib.sha256(raw).hexdigest()[:40]

    def action_bmcat_regenerate_token(self):
        self.ensure_one()
        self.bmcat_token = self._bmcat_generate_token()

    def action_bmcat_export(self):
        self.ensure_one()
        products = self.env['product.template'].search([
            ('catalog_ids', 'in', self.id),
        ])
        if not products:
            raise exceptions.UserError(
                _('No products found in this catalog.'))
        xml_content = self._bmcat_generate_xml(products)
        self._bmcat_store_file(xml_content)
        return {
            'type': 'ir.actions.act_url',
            'url': '/bmcat/%s/download' % self.bmcat_token,
            'target': 'self',
        }

    def _bmcat_store_file(self, xml_content):
        self.ensure_one()
        now = fields.Datetime.now()
        self.write({
            'bmcat_file': base64.b64encode(xml_content),
            'bmcat_filename': 'catalog_%s.xml' % self.id,
            'bmcat_generated_at': now,
            'bmcat_file_size': len(xml_content),
        })

    def _bmcat_get_stock_qty(self, product):
        self.ensure_one()
        if self.bmcat_stock_mode == 'none':
            return None
        product_variant = product.product_variant_id
        if not product_variant:
            return 0.0
        locations = self.bmcat_stock_location_ids
        if self.bmcat_stock_mode == 'real':
            if locations:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', product_variant.id),
                    ('location_id', 'child_of', locations.ids),
                ])
                return sum(quants.mapped('quantity'))
            return product_variant.qty_available
        if self.bmcat_stock_mode == 'forecast':
            if locations:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', product_variant.id),
                    ('location_id', 'child_of', locations.ids),
                ])
                return sum(quants.mapped('forecasted_quantity'))
            return product_variant.virtual_available
        if self.bmcat_stock_mode == 'boolean':
            if locations:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', product_variant.id),
                    ('location_id', 'child_of', locations.ids),
                ])
                total = sum(quants.mapped('quantity'))
                return total > 0.0
            return product_variant.qty_available > 0.0
        return None

    def _bmcat_generate_xml(self, products):
        namespaces = {None: BMEATCAT_NS, 'xsi': XSI_NS}
        schema_location = (
            f'{BMEATCAT_NS} http://www.bmecat.org/bmecat/2005/BMECat.xsd')
        root = etree.Element(
            '{' + BMEATCAT_NS + '}BMECAT', nsmap=namespaces)
        root.set('{%s}schemaLocation' % XSI_NS, schema_location)
        root.set('version', '2005')
        header = etree.SubElement(root, 'HEADER')
        catalog = etree.SubElement(header, 'CATALOG')
        etree.SubElement(catalog, 'LANGUAGE').text = 'spa'
        etree.SubElement(catalog, 'CATALOG_NAME').text = self._bmcat_safe_text(
            self.name)
        etree.SubElement(catalog, 'CATALOG_VERSION').text = '1.0'
        etree.SubElement(catalog, 'DATETIME').text = (
            fields.Datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
        etree.SubElement(catalog, 'CURRENCY').text = 'EUR'
        t_new_catalog = etree.SubElement(root, 'T_NEW_CATALOG')
        sup_info = etree.SubElement(t_new_catalog, 'SUPPLIER_INFO')
        supplier = self.env.company
        etree.SubElement(sup_info, 'SUPPLIER_NAME').text = (
            self._bmcat_safe_text(supplier.name))
        for product in products:
            self._bmcat_add_article(t_new_catalog, product)
        return etree.tostring(
            root, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def _bmcat_add_article(self, parent, product):
        article = etree.SubElement(parent, 'ARTICLE')
        etree.SubElement(article, 'SUPPLIER_AID').text = \
            self._bmcat_safe_text(product.default_code or str(product.id))
        etree.SubElement(article, 'ARTICLE_NO').text = \
            self._bmcat_safe_text(product.default_code or str(product.id))
        etree.SubElement(article, 'EAN').text = \
            self._bmcat_safe_text(product.barcode or '')
        details = etree.SubElement(article, 'ARTICLE_DETAILS')
        etree.SubElement(details, 'DESCRIPTION_SHORT').text = \
            self._bmcat_safe_text(product.name)
        if product.description_sale:
            desc_long = etree.SubElement(details, 'DESCRIPTION_LONG')
            desc_long.text = etree.CDATA(
                self._bmcat_safe_text(product.description_sale))
        if product.categ_id:
            misc = etree.SubElement(article, 'ARTICLE_ORDER_DETAILS')
            etree.SubElement(misc, 'ORDER_UNIT').text = 'C62'
            classification = etree.SubElement(article, 'CLASSIFICATION')
            etree.SubElement(
                classification, 'CLASSIFICATION_GROUP_ID').text = (
                    self._bmcat_safe_text(product.categ_id.name))
            etree.SubElement(
                classification, 'CLASSIFICATION_GROUP_NAME').text = (
                    self._bmcat_safe_text(
                        product.categ_id.complete_name.replace('/', ' > ')
                    ))
        prices = etree.SubElement(article, 'ARTICLE_PRICE_DETAILS')
        price_elem = etree.SubElement(prices, 'ARTICLE_PRICE')
        price_elem.set('price_type', 'net_list')
        lst_price = product.list_price if product.list_price else 0.0
        etree.SubElement(price_elem, 'PRICE_AMOUNT').text = '%.2f' % lst_price
        etree.SubElement(price_elem, 'PRICE_CURRENCY').text = 'EUR'
        if product.weight:
            features = etree.SubElement(article, 'PRODUCT_FEATURES')
            ref = etree.SubElement(features, 'REFERENCE_FEATURE_SYSTEM')
            ref.set('name', 'WEIGHT')
            etree.SubElement(ref, 'REFERENCE_FEATURE_GROUP_ID').text = 'WEIGHT'
            fname = etree.SubElement(ref, 'REFERENCE_FEATURE_GROUP_NAME')
            fname.text = 'Weight'
            feat = etree.SubElement(ref, 'FEATURE')
            feat.set('fvalue', str(product.weight))
            etree.SubElement(feat, 'FNAME').text = 'Weight (kg)'
            etree.SubElement(feat, 'FVALUE').text = '%s kg' % str(
                product.weight)
        if product.image_1920:
            mime = etree.SubElement(article, 'MIME_INFO')
            mime_obj = etree.SubElement(mime, 'MIME')
            etree.SubElement(mime_obj, 'MIME_TYPE').text = 'image/png'
            etree.SubElement(mime_obj, 'MIME_SOURCE').text = 'http'
            etree.SubElement(mime_obj, 'MIME_DESCR').text = \
                self._bmcat_safe_text(product.name)
            etree.SubElement(mime_obj, 'MIME_ALTERNATIVE_TEXT').text = \
                self._bmcat_safe_text(product.name)
        stock = self._bmcat_get_stock_qty(product)
        if stock is not None:
            article_stock = etree.SubElement(article, 'ARTICLE_STOCK')
            if self.bmcat_stock_mode == 'boolean':
                etree.SubElement(
                    article_stock, 'STOCK').text = 'yes' if stock else 'no'
            else:
                etree.SubElement(
                    article_stock, 'STOCK').text = str(stock)
            etree.SubElement(
                article_stock, 'STOCK_UNIT').text = str(product.uom_id.name)

    def _bmcat_cache_valid(self):
        self.ensure_one()
        if not self.bmcat_cache_hours:
            return False
        if not self.bmcat_generated_at or not self.bmcat_file:
            return False
        limit = fields.Datetime.now() - timedelta(hours=self.bmcat_cache_hours)
        return self.bmcat_generated_at >= limit

    def _bmcat_get_or_generate(self):
        self.ensure_one()
        if self._bmcat_cache_valid():
            return base64.b64decode(self.bmcat_file)
        products = self.env['product.template'].search([
            ('catalog_ids', 'in', self.id),
        ])
        if not products:
            return False
        xml_content = self._bmcat_generate_xml(products)
        self._bmcat_store_file(xml_content)
        return xml_content
