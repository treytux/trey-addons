###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    contract_id = fields.Many2one(
        comodel_name='contract.contract',
        string='Contract',
        domain="[('partner_id', '=', partner_id)]",
    )

    @api.constrains('contract_id')
    def _check_contract_partner(self):
        if not self.contract_id or not self.contract_id.partner_id:
            return
        if self.contract_id.partner_id != self.partner_id:
            raise ValidationError(_(
                'The contract and the project must belong to the same partner.'
            ))
