###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ContractLine(models.Model):
    _inherit = 'contract.line'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='contract_id.company_id',
        store=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        related='contract_id.partner_id',
        store=True,
    )
