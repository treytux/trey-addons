###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    recurring_total = fields.Float(
        string='Recurring Total',
        compute='_compute_recurring_total',
        digits=dp.get_precision('Account'),
        store=True,
    )

    @api.depends('contract_line_ids.recurring_subtotal')
    def _compute_recurring_total(self):
        for contract in self:
            contract.recurring_total = sum(
                contract.contract_line_ids.mapped('recurring_subtotal'))
