###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    team_pricelist_ids = fields.One2many(
        comodel_name='product.team.pricelist',
        inverse_name='team_id',
        string='Sales Team Pricelist',
    )
