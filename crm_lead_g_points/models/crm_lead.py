###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    g_points = fields.Many2many(
        comodel_name='crm.lead.g_point',
        string='G Points',
    )
