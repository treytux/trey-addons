###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmLeadGPoint(models.Model):
    _name = 'crm.lead.g_point'
    _description = 'Crm G points'

    name = fields.Char(
        string='Name',
        required=True,
    )
