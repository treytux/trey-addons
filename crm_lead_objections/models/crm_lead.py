###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    objection_ids = fields.Many2many(
        string='Objections',
        comodel_name='crm.lead.objection',
    )
