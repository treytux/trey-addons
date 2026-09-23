###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_note = fields.Html(
        string='Default sale note',
        help='Set default terms and conditions for sales orders',
    )
