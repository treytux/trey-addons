###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def invoice_line_move_line_get(self):
        res = []
        for line in self.invoice_line_ids:
            if not line.account_id or line.quantity == 0:
                continue
            tax_ids = []
            for tax in line.invoice_line_tax_ids:
                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))
            analytic_tag_ids = [
                (4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids
            ]
            move_line_dict = {
                'invl_id': line.id,
                'type': 'src',
                'name': line.name,
                'price_unit': line.price_unit,
                'quantity': line.quantity,
                'price': line.price_subtotal,
                'account_id': line.account_id.id,
                'product_id': line.product_id.id,
                'uom_id': line.uom_id.id,
                'account_analytic_id': line.account_analytic_id.id,
                'analytic_tag_ids': analytic_tag_ids,
                'tax_ids': tax_ids,
                'invoice_id': self.id,
                'subvention_id': line.subvention_id.id,
                'subvention_percent': line.subvention_percent,

            }
            res.append(move_line_dict)
        return res

    def line_get_convert(self, line, part):
        res = super().line_get_convert(line, part)
        res['subvention_id'] = line.get('subvention_id', None)
        res['subvention_percent'] = line.get('subvention_percent', 0)
        return res
