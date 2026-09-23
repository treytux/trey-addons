###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
import logging
import math
import xml.etree.ElementTree as ET
from datetime import date

import odoo.addons.decimal_precision as dp
import requests
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_log = logging.getLogger(__name__)


class ConnectorSimulatorSale(models.TransientModel):
    _inherit = 'connector.simulator.sale'

    supplier_mode = fields.Selection(
        selection_add=[
            ('comafe', 'Comafe'),
        ]
    )
    simulate_order_date_comafe = fields.Date(
        string='Simulate order date Comafe',
    )

    def check_comafe_credentials(self, connector):
        if not connector.erp_user_comafe:
            raise ValidationError(_('ERP user not set'))
        if not connector.erp_password_comafe:
            raise ValidationError(_('ERP password not set'))
        if not connector.customer_code_comafe:
            raise ValidationError(_('Customer code not set'))
        if not connector.customer_office_comafe:
            raise ValidationError(_('Office not set'))
        if not connector.customer_key_comafe:
            raise ValidationError(_('Customer key not set'))

    def get_api_comafe_supplier_qty(self, response, product_code):
        content = response.text
        lines = content.split('\n')
        if len(lines) == 1:
            raise ValidationError(_(
                'Product code %s not found in api response') % product_code)
        elif len(lines) > 1:
            return int(float(lines[1].split(';')[1]))

    def get_weekly_prices_comafe(self, url_base):
        current_week = date.today().isocalendar()[1] - 1
        url_price = (
            f'{url_base}&TD=AS-AR&AX={current_week}&TA=XML&PT=DAT&'
            f'NF=s{current_week}.dat&FD=FIC'
        )
        _log.info('Comafe WS: Requesting and processing products price')
        response = requests.get(url=url_price)
        if response.status_code != 200:
            raise ValidationError(_(
                'Error when communicating with API: %s') %
                response.content.decode('utf-8'))
        tree = ET.fromstring(response.content)
        prices_week_dict = {
            product.find('CODIGO').text: product.find('PRECIO').text
            for product in tree.findall('ARTICULO')
        }
        return prices_week_dict

    def get_url_base_comafe(self, connector):
        url_base = 'https://intranet.comafe.es/varios/service.php?'\
                   'US=%s&PW=%s&SO=%s&DE=%s&CC=%s&BN=COM'
        return url_base % (
            connector.erp_user_comafe, connector.erp_password_comafe,
            connector.customer_code_comafe, connector.customer_office_comafe,
            connector.customer_key_comafe)

    def send_stock_request_comafe(self, line, url_base, supplierinfos):
        product_code = supplierinfos[0].product_code
        url_stock = (
            f'{url_base}&TD=STCK&FD=FIC&NF=stock.txt&AX=914&PT={product_code}'
        )
        _log.info('Comafe WS: Requesting and processing product %s stock' % (
            supplierinfos[0].product_code))
        response = requests.post(url=url_stock)
        if response.status_code != 200:
            raise ValidationError(_(
                'Error when communicating with API: %s') %
                response.content.decode('utf-8'))
        try:
            qty_available = self.get_api_comafe_supplier_qty(
                response, product_code)
            line.write({
                'qty_available_comafe': qty_available,
                'msg_comafe': _('Stock obtained by API Comafe'),
            })
        except ValidationError as e:
            line.msg_comafe = e.args[0]

    @api.multi
    def action_to_step_2(self):
        res = super().action_to_step_2()
        connector = self.env['connector.supplier'].search([
            ('supplier_mode', '=', 'comafe'),
        ], limit=1)
        if not connector:
            return res
        self.check_comafe_credentials(connector)
        prices_dict = json.loads(connector.prices_data_comafe)
        packs_dict = json.loads(connector.packaging_data_comafe)
        url_base = self.get_url_base_comafe(connector)
        prices_week_dict = self.get_weekly_prices_comafe(url_base)
        for line in self.lines:
            supplierinfos = line.product_id.seller_ids.filtered(
                lambda sp: sp.name == connector.supplier_id and sp.product_code)
            if not supplierinfos:
                line.msg_comafe = _('No supplier rate or product code found')
                continue
            self.send_stock_request_comafe(line, url_base, supplierinfos)
            item_price = prices_dict.get(
                supplierinfos[0].product_code, False) or (
                prices_week_dict.get(supplierinfos[0].product_code, False))
            if item_price:
                line.write({
                    'price_unit_comafe': item_price,
                    'total_price_comafe': item_price * line.product_uom_qty,
                    'msg_comafe': _('Rate and stock obtained by API Comafe'),
                    'price_fetch_error_comafe': False,
                })
                if line.price_unit_comafe != supplierinfos[0].price:
                    line.price_updated_comafe = True
            pack_item = packs_dict.get(supplierinfos[0].product_code, False)
            if pack_item:
                line.packaging_comafe = pack_item
            else:
                line.packaging_comafe = supplierinfos[0].min_qty
        _log.info('Comafe WS: End simulation order %s' % self.order_id.name)
        return res

    @api.multi
    def action_to_step_done(self):
        res = super().action_to_step_done()
        connector = self.env['connector.supplier'].search([
            ('supplier_mode', '=', 'comafe'),
        ], limit=1)
        for line in self.lines.filtered(
                lambda ln: ln.price_updated_comafe and not (
                    ln.price_fetch_error_comafe)):
            supplierinfos = line.product_id.seller_ids.filtered(
                lambda sp: sp.name == connector.supplier_id)
            supplierinfos[0].price = line.price_unit_comafe
            line.sale_line_id.standard_price = (
                line.sale_line_id.product_id.standard_price or 0)
            line.sale_line_id.product_id_change_margin()
        msg = _('Prices simulated with supplier connector')
        self.order_id.message_post(body=msg)
        return res


class ConnectorSimulatorSaleLine(models.TransientModel):
    _inherit = 'connector.simulator.sale.line'

    price_unit_comafe = fields.Float(
        string='Cost Comafe',
        digits=dp.get_precision('Product Price'),
    )
    total_price_comafe = fields.Float(
        string='Total cost',
    )
    qty_available_comafe = fields.Float(
        string='Qty available Comafe',
    )
    packaging_comafe = fields.Float(
        string='Packaging Comafe',
    )
    multiple_qty_comafe = fields.Float(
        string='Multiple qty Comafe',
        compute='_compute_line_color',
    )
    msg_comafe = fields.Char(
        string='Message',
    )
    price_updated_comafe = fields.Boolean(
        string='Price updated',
    )
    price_fetch_error_comafe = fields.Boolean(
        string='Price fetch error',
        default=True,
    )

    def get_multiple(self, num_a, num_b):
        return math.ceil(num_a / num_b) * num_b

    def _compute_line_color(self):
        res = super()._compute_line_color()
        for line in self:
            if line.sale_id.supplier_mode != 'comafe':
                continue
            if line.qty_available_comafe == 0:
                line.line_color = 'red'
                line.multiple_qty_comafe = 0
                continue
            line.multiple_qty_comafe = (
                line.packaging_comafe if (
                    line.product_uom_qty <= line.packaging_comafe)
                else self.get_multiple(
                    line.product_uom_qty, line.packaging_comafe)
            )
            if line.multiple_qty_comafe <= line.qty_available_comafe:
                line.line_color = 'green' if (
                    line.product_uom_qty % line.packaging_comafe == 0) else (
                    'blue')
            else:
                line.line_color = 'orange'
        return res
