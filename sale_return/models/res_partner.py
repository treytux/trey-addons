###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    return_penalty_percent = fields.Float(
        string='Penalty percent for returns (%)',
    )
