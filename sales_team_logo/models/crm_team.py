###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Team(models.Model):
    _inherit = 'crm.team'

    logo = fields.Binary(
        string='Team logo',
    )
