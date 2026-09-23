###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'
    logo = fields.Binary(
        string='Team Logo',
        attachment=True,
        help='Custom team logo used in printed sale documents.',
    )
