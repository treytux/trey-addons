###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime
import io
import json
import logging
import os
import xml.etree.ElementTree as ET
import zipfile

import requests
from odoo import _, fields, models

_log = logging.getLogger(__name__)


class ConnectorSupplier(models.Model):
    _inherit = 'connector.supplier'

    supplier_mode = fields.Selection(
        selection_add=[
            ('comafe', 'Comafe'),
        ],
    )
    erp_user_comafe = fields.Char(
        string='ERP Comafe user',
    )
    erp_password_comafe = fields.Char(
        string='ERP Comafe password',
    )
    customer_code_comafe = fields.Char(
        string='Comafe customer code',
    )
    customer_office_comafe = fields.Char(
        string='Comafe customer office',
    )
    customer_key_comafe = fields.Char(
        string='Comafe customer key',
    )
    prices_data_comafe = fields.Text(
        string='Product data Comafe',
    )
    packaging_data_comafe = fields.Text(
        string='Packaging data Comafe',
    )
    last_price_update_comafe = fields.Datetime(
        string='Last price update Comafe',
    )
    last_auto_price_update_comafe = fields.Datetime(
        string='Last automatic price update Comafe',
    )
    file_extract_path_comafe = fields.Char(
        string='File extract path Comafe',
    )

    def automatic_website_publish_comafe_products(self):
        connector = self.env['connector.supplier'].search([
            ('supplier_mode', '=', 'comafe'),
        ], limit=1)
        if not connector or not connector.file_extract_path_comafe:
            return
        prices_dict = json.loads(connector.prices_data_comafe)
        supplierinfos = self.env['product.supplierinfo'].search([
            ('name', '=', connector.supplier_id.id),
            ('product_code', '!=', False),
        ])
        supplierinfos = supplierinfos.filtered(
            lambda sp: len(sp.product_tmpl_id.seller_ids.mapped('name')) == 1)
        _log.info('Automatic publish Comafe products')
        for index, supplierinfo in enumerate(supplierinfos, start=1):
            _log.info(
                '[%s/%s] %s' % (
                    index, len(supplierinfos), supplierinfo.product_code))
            value = prices_dict.get(supplierinfo.product_code, False)
            if not value:
                supplierinfo.product_tmpl_id.website_published = False
                msg = _('Product archived automatically by the scheduled Comafe'
                        ' task checking stock availability via API.')
                supplierinfo.product_tmpl_id.message_post(body=msg)

    def automatic_update_prices_comafe_cron(self):
        connector = self.env['connector.supplier'].search([
            ('supplier_mode', '=', 'comafe'),
        ], limit=1)
        if not connector or not connector.file_extract_path_comafe:
            return
        prices_dict = json.loads(connector.prices_data_comafe)
        supplier_id = connector.supplier_id.id
        all_codes = list(prices_dict.keys())
        query = '''
            SELECT id, product_code
            FROM product_supplierinfo
            WHERE product_code = ANY(%s)
            AND name = %s
        '''
        self.env.cr.execute(query, (all_codes, supplier_id))
        rows = self.env.cr.fetchall()
        supplierinfo_by_code = {
            code: self.env['product.supplierinfo'].browse(sid)
            for sid, code in rows
        }
        _log.info('Automatic update price Comafe supplierinfos')
        for index, (key, value) in enumerate(prices_dict.items(), start=1):
            _log.info('[%s/%s] %s' % (index, len(prices_dict), key))
            supplierinfo = supplierinfo_by_code.get(key)
            if supplierinfo:
                supplierinfo.write({
                    'price': value,
                })
        connector.last_auto_price_update_comafe = fields.Datetime.now()

    def get_prices_comafe_cron(self):
        connector = self.env['connector.supplier'].search([
            ('supplier_mode', '=', 'comafe'),
        ], limit=1)
        if not connector or not connector.file_extract_path_comafe:
            return
        url_base = 'https://intranet.comafe.es/varios/service.php?'\
                   'US=%s&PW=%s&SO=%s&DE=%s&CC=%s&BN=COM'
        url_base = url_base % (
            connector.erp_user_comafe, connector.erp_password_comafe,
            connector.customer_code_comafe, connector.customer_office_comafe,
            connector.customer_key_comafe)
        current_week = datetime.date.today().isocalendar()[1] - 1
        url_price = '&TD=AS-AR&AX=CO&TA=XML&PT=ZIP&NF=s{0}.zip&FD=FIC'.format(
            current_week)
        url_price = url_base + url_price
        response = requests.get(url=url_price)
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(connector.file_extract_path_comafe)
            files = os.listdir(connector.file_extract_path_comafe)
            xml_file = [file for file in files if file.endswith('.xml')][0]
            tree = ET.parse(
                os.path.join(connector.file_extract_path_comafe, xml_file))
            root = tree.getroot()
            products_dict = {
                product.find('CODIGO').text: float(
                    product.find('PRECIO').text.replace(',', '.'))
                for product in root.findall('ARTICULO')
            }
            packs_dict = {
                product.find('CODIGO').text: float(
                    product.find('VENTA_UDS').text.replace(',', '.'))
                for product in root.findall('ARTICULO')
            }
            connector.write({
                'prices_data_comafe': json.dumps(products_dict),
                'packaging_data_comafe': json.dumps(packs_dict),
                'last_price_update_comafe': fields.Datetime.now(),
            })
