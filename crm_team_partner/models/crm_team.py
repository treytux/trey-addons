###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
    )
