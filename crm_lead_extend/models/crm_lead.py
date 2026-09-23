###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    decision_makers_ids = fields.Many2many(
        string='Decision-makers',
        comodel_name='res.partner',
    )
    quarter_decision = fields.Integer(
        string='Quarter decision',
    )
    year_decision = fields.Integer(
        string='Year decision',
    )
    quarter_implementation = fields.Integer(
        string='Quarter implementation',
    )
    year_implementation = fields.Integer(
        string='Year implementation',
    )
    budget = fields.Float(
        string='Budget',
    )
    employes_number = fields.Integer(
        string='Employes number',
    )
    headquarters_number = fields.Integer(
        string='Headquarters number',
    )
    facturation = fields.Float(
        string='Facturation',
    )
