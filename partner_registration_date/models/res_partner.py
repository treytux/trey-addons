###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    registration_date = fields.Date(
        string='Registration date',
        default=fields.Date.today)
