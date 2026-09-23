###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    website_sale_stock_qty_mode = fields.Selection(
        selection=[
            ('available', 'Available Stock'),
            ('real', 'Real Stock'),
            ('forecasted', 'Forecasted Stock'),
        ],
        string='eCommerce Stock Mode',
        default='available',
        required=True,
        help='Choose the stock quantity used by the online store.',
    )

    def _get_website_sale_stock_qty_mode(self):
        self.ensure_one()
        return self.website_sale_stock_qty_mode or 'available'
