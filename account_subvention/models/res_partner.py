###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    subvention_percent = fields.Float(
        string='Subvention (%)',
        track_visibility='onchange',
    )
    subvention_id = fields.Many2one(
        comodel_name='account.subvention',
        string='Subvention',
        track_visibility='onchange',
    )
