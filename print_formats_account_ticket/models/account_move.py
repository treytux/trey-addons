###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_tax_amount_by_group(self):
        tax_amount_by_group = {}
        for line in self.line_ids:
            for tax in line.tax_ids:
                if tax.tax_group_id.name not in tax_amount_by_group:
                    tax_amount_by_group[tax.tax_group_id.name] = [0, 0, 0, 0, 0]
                tax_amount_by_group[tax.tax_group_id.name][0] = (
                    tax.tax_group_id.name)
                tax_amount_by_group[tax.tax_group_id.name][3] += (
                    line.price_total - line.price_subtotal)
                tax_amount_by_group[tax.tax_group_id.name][4] += (
                    line.price_subtotal)
        return tax_amount_by_group.values()
