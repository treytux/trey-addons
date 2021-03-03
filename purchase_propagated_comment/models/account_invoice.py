###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    purchase_propagated_comment = fields.Text(
        string='Purchase Propagated Comment',
        compute='_compute_purchase_comment',
    )

    @api.depends('invoice_line_ids', 'invoice_line_ids.purchase_id')
    def _compute_purchase_comment(self):
        for invoice in self:
            comments = invoice.invoice_line_ids.mapped(
                'purchase_id.purchase_propagated_comment')
            invoice.purchase_propagated_comment = '\n'.join(
                c for c in comments if c)
