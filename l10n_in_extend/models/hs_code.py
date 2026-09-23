###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class HSCode(models.Model):
    _inherit = 'hs.code'

    rate = fields.Char(
        string='Rate',
    )
