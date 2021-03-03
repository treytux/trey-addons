###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    cookiebot_id = fields.Char(
        string='Cookiebot Key',
        help='This field holds the ID,'
        ' needed for Cookiebot functionality.',
    )
