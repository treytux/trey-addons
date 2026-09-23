###############################################################################
# For copyright and license notices, see __manifest__.py file
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    sale_order_skip_stock_picking = fields.Boolean(
        string='Do not create delivery orders on confirmation',
        help='If enabled, sale orders from this website will not create '
             'stock moves or delivery orders when confirmed.',
    )
