###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    red_flag_ids = fields.Many2many(
        string='Red flags',
        comodel_name='crm.lead.red.flag',
    )
