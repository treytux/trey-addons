###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    smartsupp_key = fields.Char(
        string='Installation Code',
        help='This field holds the installation code,'
        ' needed for Smartsupp chat functionality.',
    )
