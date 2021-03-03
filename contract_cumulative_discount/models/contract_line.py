###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ContractLine(models.Model):
    _inherit = 'contract.line'

    @api.multi
    def _prepare_invoice_line(self, invoice_id=False, invoice_values=False):
        res = super()._prepare_invoice_line(
            invoice_id=invoice_id, invoice_values=invoice_values)
        res.update({
            'multiple_discount': self.multiple_discount,
            'discount_name': self.discount_name,
        })
        return res
