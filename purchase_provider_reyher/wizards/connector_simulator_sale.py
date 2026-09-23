###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
import logging
import time

import requests
from odoo import _, fields, models
from odoo.exceptions import ValidationError

_log = logging.getLogger(__name__)


class ConnectorSimulatorSale(models.TransientModel):
    _inherit = 'connector.simulator.sale'

    supplier_mode = fields.Selection(
        selection_add=[
            ('reyher', 'Reyher'),
        ],
    )
    simulate_order_date_reyher = fields.Date(
        string='Simulate order date Reyher',
    )

    def action_to_step_2(self):
        self.ensure_one()
        res = super().action_to_step_2()
        connector = self.env['connector.supplier'].search([
            ('supplier_mode', '=', 'reyher'),
        ], limit=1)
        if not connector:
            return res
        if not connector.token_reyher or (
                fields.Date.today() > connector.token_validity_date_reyher):
            url_authenticate = (
                'https://rio.reyher.de/rest/reyher_int_de/V1/integration'
                '/customer/token')
            data = {
                'username': connector.username_ws,
                'password': connector.password_ws,
            }
            headers = {
                'Content-Type': 'application/json',
            }
            _log.info('Reyher API: Login')
            response = requests.post(
                url=url_authenticate, headers=headers, data=json.dumps(data))
            _log.info('Reyher API: Processing login token')
            if response.status_code != 200:
                raise ValidationError(_(
                    'Error when communicating with API: %s') %
                    response.content.decode('utf-8'))
            connector.token_reyher = response.content.decode('utf-8')
        url_simulate = (
            'https://rio.reyher.de/rest/reyher_int_de/V1/sapordersimulate/mine'
            '/getOrdersimulate')
        headers = {
            'Authorization': 'Bearer %s' % connector.token_reyher,
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }
        _log.info('Reyher API: Simulate order %s' % self.order_id.name)
        for line in self.lines:
            start = time.time()
            data = {
                'items': [],
            }
            supplierinfos = line.product_id.seller_ids.filtered(
                lambda sp: sp.partner_id == connector.supplier_id)
            if not supplierinfos:
                continue
            vals = {
                'position': 0,
                'sku': str(supplierinfos[0].product_code).zfill(15),
                'quantity': int(line.product_uom_qty),
            }
            data['items'].append(vals)
            time.sleep(5)
            response = requests.post(
                url=url_simulate, headers=headers, data=json.dumps(data))
            if response.status_code != 200:
                raise ValidationError(_(
                    'Error when communicating with API: %s') % (
                    response.content.decode('utf-8')))
            content = json.loads(response.content)
            if not content:
                raise ValidationError(_('Error: not content found in response'))
            if content[0]['StatusCode'] == 0:
                item = content[0]['Payload']['Items'][0]
                line.write({
                    'price_unit_reyher': item['Price'] / 100,
                    'total_price_reyher': item['PositionPrice'],
                    'qty_available_reyher': item['QuantityAvailable'],
                    'currency_reyher': item['Currency'],
                    'msg_reyher': _('Rate obtained by API Reyher'),
                    'price_fetch_error': False,
                })
                if line.price_unit_reyher != supplierinfos[0].price:
                    line.update_cost_reyher = True
                continue
            if content[0]['StatusCode'] != 0:
                if supplierinfos[0].product_code:
                    line.msg_reyher = '%s: %s' % (
                        content[0]['StatusCode'],
                        content[0]['Statusinformation'])
                vals['sku'] = str(
                    supplierinfos[0].product_tmpl_id.default_code).zfill(15)
                data['items'] = []
                data['items'].append(vals)
                end = time.time()
                dif = int(end - start)
                if dif < 5:
                    time.sleep(5 - dif)
                response = requests.post(
                    url=url_simulate, headers=headers, data=json.dumps(data))
                if response.status_code != 200:
                    raise ValidationError(_(
                        'Error when communicating with API: %s') % (
                        response.content.decode('utf-8')))
                content = json.loads(response.content)
                if not content:
                    raise ValidationError(_(
                        'Error: not content found in response'))
                if content[0]['StatusCode'] != 0:
                    if line.msg_reyher:
                        line.msg_reyher = line.msg_reyher + ', ' + '%s: %s' % (
                            content[0]['StatusCode'],
                            content[0]['Statusinformation'])
                    else:
                        line.msg_reyher = '%s: %s' % (
                            content[0]['StatusCode'],
                            content[0]['Statusinformation'])
        _log.info('Reyher API: End simulation order %s' % self.order_id.name)
        return res

    def action_to_step_done(self):
        self.ensure_one()
        res = super().action_to_step_done()
        connector = self.env['connector.supplier'].search([
            ('supplier_mode', '=', 'reyher'),
        ], limit=1)
        for line in self.lines.filtered(
                lambda ln: ln.update_cost_reyher and not ln.price_fetch_error):
            supplierinfos = line.product_id.seller_ids.filtered(
                lambda sp: sp.partner_id == connector.supplier_id)
            supplierinfos[0].price = line.price_unit_reyher
            line.sale_line_id.standard_price = (
                line.sale_line_id.product_id.standard_price or 0)
        msg = _('Prices simulated with supplier connector on %s by %s') % (
            fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            self.env.user.name)
        self.order_id.message_post(body=msg)
        return res


class ConnectorSimulatorSaleLine(models.TransientModel):
    _inherit = 'connector.simulator.sale.line'

    price_unit_reyher = fields.Float(
        string='Cost Reyher',
        help='Price unit excluding discounts and surcharges',
        digits='Product Price',
    )
    total_price_reyher = fields.Float(
        string='Total price',
        help='Total price including discounts and surcharges',
        digits='Product Price',
    )
    qty_available_reyher = fields.Float(
        string='Qty Reyher',
    )
    currency_reyher = fields.Char(
        string='Currency',
    )
    msg_reyher = fields.Char(
        string='Message',
    )
    update_cost_reyher = fields.Boolean(
        string='Update cost Reyher',
    )
    price_fetch_error = fields.Boolean(
        string='Price fetch error',
        default=True,
    )

    def _compute_line_color(self):
        res = super()._compute_line_color()
        for line in self:
            if line.sale_id.supplier_mode != 'reyher':
                continue
            if line.qty_available_reyher > line.product_uom_qty:
                line.line_color = 'blue'
            elif line.qty_available_reyher == line.product_uom_qty:
                line.line_color = 'green'
            elif line.qty_available_reyher == 0:
                line.line_color = 'red'
            else:
                line.line_color = 'orange'
        return res
