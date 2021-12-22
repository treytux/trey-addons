###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    nexmart_apikey = fields.Char(
        string='Nexmart API Key',
        help='Type here your Nexmart partner API Key',
    )
