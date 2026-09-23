###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, fields, models

try:
    from woocommerce import API
except ImportError:
    API = None


class Website(models.Model):
    _inherit = 'website'

    is_woo = fields.Boolean(
        string='Is a WooCommerce',
    )
    woo_sync_stock_realtime = fields.Boolean(
        string='Sync stock in realtime',
    )
    woo_export_method = fields.Selection(
        selection=[
            ('manual', 'Manual'),
            ('queue', 'On save, using queue job manager (recomended)'),
            ('orm', 'On save, usign Odoo ORM'),
        ],
        string='Export Method',
        default='queue',
    )
    woo_url = fields.Char(
        string='Woo URL',
    )
    woo_odoo_url = fields.Char(
        string='Odoo URL',
    )
    woo_version = fields.Char(
        string='Version',
        default='wc/v3',
    )
    woo_consumer_key = fields.Char(
        string='Consumer Key',
    )
    woo_consumer_secret = fields.Char(
        string='Consumer Secret',
    )
    woo_timeout = fields.Integer(
        string='Timeout',
        default=5,
    )
    woo_date_last_sale = fields.Datetime(
        string='Last sale imported',
        help=(
            'Date and time of the last imported order. Orders after this date '
            'will be imported, if you want to import all orders make sure '
            'this value is empty'
        ),
    )
    woo_catalog_ids = fields.Many2many(
        comodel_name='product.catalog',
        relation='website2product_catalog_rel',
        column1='website_id',
        column2='product_catalog_id',
        string='Catalogs',
        help=(
            'Export only selected catalogs, if this field is empty, export '
            'all products'
        ),
    )

    def woo_api_get(self):
        self.ensure_one()
        if not API:
            raise exceptions.UserError(
                _('Please install woocommerce python library'))
        return API(
            url=self.woo_url,
            version=self.woo_version,
            query_string_auth=True,
            consumer_key=self.woo_consumer_key,
            consumer_secret=self.woo_consumer_secret,
            timeout=self.woo_timeout,
        )

    def action_open_woo_sync(self):
        self.ensure_one()
        wizard = self.env['woocommerce.sync'].create({
            'website_id': self.id,
        })
        action = self.env.ref(
            'woocommerce_connector.woocommerce_sync_website_action')
        res = action.read()[0]
        res.update({
            'res_id': wizard.id,
            'view_mode': 'form',
        })
        return res

    def action_open_woo_sale_import(self):
        self.ensure_one()
        wizard = self.env['woocommerce.sale.import'].create({
            'website_id': self.id,
        })
        wizard.action_count()
        action = self.env.ref(
            'woocommerce_connector.woocommerce_sale_import_website_action')
        res = action.read()[0]
        res.update({
            'res_id': wizard.id,
            'view_mode': 'form',
        })
        return res

    def action_view_logs(self):
        self.ensure_one()
        action = self.env.ref('woocommerce_connector.woocommerce_log_action')
        action = action.read()[0]
        action['domain'] = [('website_id', '=', self.id)]
        action['context'] = {'default_website_id': self.id}
        return action
