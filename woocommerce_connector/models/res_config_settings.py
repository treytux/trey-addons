###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_woo = fields.Boolean(
        related='website_id.is_woo',
        readonly=False,
    )
    woo_export_method = fields.Selection(
        related='website_id.woo_export_method',
        readonly=False,
    )
    woo_sync_stock_realtime = fields.Boolean(
        related='website_id.woo_sync_stock_realtime',
        readonly=False,
    )
    woo_url = fields.Char(
        related='website_id.woo_url',
        readonly=False,
    )
    woo_odoo_url = fields.Char(
        related='website_id.woo_odoo_url',
        readonly=False,
    )
    woo_version = fields.Char(
        related='website_id.woo_version',
        readonly=False,
        default='wc/v3',
    )
    woo_consumer_key = fields.Char(
        related='website_id.woo_consumer_key',
        readonly=False,
    )
    woo_consumer_secret = fields.Char(
        related='website_id.woo_consumer_secret',
        readonly=False,
    )
    woo_timeout = fields.Integer(
        related='website_id.woo_timeout',
        readonly=False,
    )
    woo_date_last_sale = fields.Datetime(
        related='website_id.woo_date_last_sale',
        string='Last sale imported',
        help=(
            'Date and time of the last imported order. Orders after this date '
            'will be imported, if you want to import all orders make sure '
            'this value is empty'
        ),
        readonly=False,
    )

    def action_open_woo_sync(self):
        return self.website_id.action_open_woo_sync()

    def action_open_woo_sale_import(self):
        return self.website_id.action_open_woo_sale_import()
