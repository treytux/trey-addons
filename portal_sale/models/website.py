###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    limit_orders_quotations = fields.Integer(
        string='Maximum number of sale orders and quotations to show',
        default=3,
    )
