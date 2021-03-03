###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    pixel_key = fields.Char(
        string='Pixel Key',
        help='This field holds the Pixel Key,'
        ' needed for Facebook Pixel functionality.',
    )
