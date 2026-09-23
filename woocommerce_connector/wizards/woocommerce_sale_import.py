###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WooCommerceSaleImport(models.TransientModel):
    _name = 'woocommerce.sale.import'
    _description = 'Wizard to import sales from WooCommerce'

    def _default_website_id(self):
        websites = self.env['website'].search([
            ('is_woo', '=', True),
        ])
        if len(websites) == 1:
            return websites
        return False

    website_id = fields.Many2one(
        comodel_name='website',
        string='Website',
        domain='[("is_woo", "=", True)]',
        default=_default_website_id,
    )
    woo_date_last_sale = fields.Datetime(
        related='website_id.woo_date_last_sale',
        string='Last sale imported',
        help=(
            'Date and time of the last imported order. Orders after this date '
            'will be imported, if you want to import all orders make sure '
            'this value is empty'
        ),
        readonly=True,
    )
    json_file = fields.Binary(
        string='JSON file',
        help='JSON file to create a sale order',
    )
    order_count = fields.Integer(
        string='Orders',
        readonly=True,
    )
    datas = fields.Text(
        string='JSON with last orders',
    )
    state = fields.Selection(
        selection=[
            ('step-online', 'Online'),
            ('step-manual', 'Manual'),
            ('step-sync', 'Sync'),
        ],
        string='State',
        default='step-online',
    )

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    @api.model
    def _get_sale_order_from_woocommerce(self, website):
        params = {
            'status': 'pending,processing,on-hold,completed,refunded',
        }
        sale_obj = self.env['sale.order']
        last_sale = website.woo_date_last_sale
        if last_sale:
            params['after'] = sale_obj.woo_format_date_to_str(last_sale)
        return sale_obj._woo_sync_import_get(website, params=params)

    def action_change_to_online(self):
        self.state = 'step-online'
        return self._reopen_view()

    def action_change_to_manual(self):
        self.state = 'step-manual'
        return self._reopen_view()

    def action_count(self):
        self.state = 'step-sync'
        datas = self._get_sale_order_from_woocommerce(self.website_id)
        self.write({
            'order_count': len(datas),
            'datas': json.dumps(datas),
        })
        return self._reopen_view()

    def action_import(self):
        if not self.website_id:
            raise UserError(_('You must select a website'))
        if not self.datas and self.json_file:
            data = base64.b64decode(self.json_file)
            data = data.decode('utf-8').replace("'", '"')
            data = json.loads(data)
            if isinstance(data, dict):
                data = [data]
            self.write({
                'order_count': 1,
                'datas': json.dumps(data),
            })
        orders = self.env['sale.order'].woo_sync_import(
            self.website_id, datas=json.loads(self.datas))
        if orders:
            orders = orders.sorted(key=lambda o: o.date_order)
            self.website_id.woo_date_last_sale = orders[-1:][0].date_order
        action = self.env.ref('sale.action_orders').read()[0]
        action['domain'] = '[("id", "in", %s)]' % orders.ids
        return action

    @api.model
    def cron_import_sale_orders(self, website_id=None):
        if website_id:
            websites = self.env['website'].browse(website_id)
        else:
            websites = self.env['website'].search([('is_woo', '=', True)])
        sale_obj = self.env['sale.order']
        for website in websites:
            datas = self._get_sale_order_from_woocommerce(website)
            orders = sale_obj.woo_sync_import(website, datas=datas)
            if orders:
                orders = orders.sorted(key=lambda o: o.date_order)
                website.woo_date_last_sale = orders[-1:][0].date_order
