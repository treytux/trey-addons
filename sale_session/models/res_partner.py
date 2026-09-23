###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    avoid_credit_sale_session = fields.Boolean(
        string='Do not sell on credit in sales sessions',
    )
