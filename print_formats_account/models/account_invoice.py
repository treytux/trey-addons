###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    qty_total = fields.Float(
        string='Total units',
        compute='_compute_qty_total',
        help='Total units of the selected products.',
    )

    @api.depends('invoice_line_ids')
    def _compute_qty_total(self):
        for invoice in self:
            invoice.qty_total = sum(invoice.invoice_line_ids.filtered(
                lambda l: l.product_id.add_to_sum_qty).mapped('quantity'))
