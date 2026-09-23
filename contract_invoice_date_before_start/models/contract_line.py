###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ContractLine(models.Model):
    _inherit = 'contract.line'

    def _compute_create_invoice_visibility(self):
        res = super()._compute_create_invoice_visibility()
        for line in self:
            if ((not line.display_type or line.is_recurring_note)
                    and line.date_start):
                line.create_invoice_visibility = bool(line.recurring_next_date)
            else:
                line.create_invoice_visibility = False
        return res
