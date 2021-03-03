###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sale_propagated_comment = fields.Text(
        string='Propagated Comment',
        compute='_compute_sale_comment',
    )

    @api.depends('invoice_line_ids', 'invoice_line_ids.sale_line_ids')
    def _compute_sale_comment(self):
        for invoice in self:
            comments = invoice.invoice_line_ids.mapped(
                'sale_line_ids.order_id.sale_propagated_comment')
            invoice.sale_propagated_comment = '\n'.join(
                c for c in comments if c)
