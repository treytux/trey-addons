###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    ignore_margin_price_limit = fields.Boolean(
        string='Ignore sales price min',
    )
