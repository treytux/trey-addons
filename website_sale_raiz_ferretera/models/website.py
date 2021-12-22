###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    raiz_ferretera_apikey = fields.Char(
        string='Raíz Ferretera API Key',
        help='Type here your Raíz Ferretera API Key',
    )
