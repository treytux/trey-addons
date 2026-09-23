###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    goods_free_amount_total = fields.Float(
        string='Goods free total',
        compute='_compute_goods_free_amount_total',
    )

    @api.depends('invoice_line_ids', 'invoice_line_ids.quantity',
                 'invoice_line_ids.price_subtotal')
    def _compute_goods_free_amount_total(self):
        for invoice in self:
            goods_free_amount_total = 0
            for line in invoice.invoice_line_ids:
                lines = line.mapped('sale_line_ids').filtered(
                    lambda ln: ln.line_goods_free_id)
                goods_free_amount_total += sum(
                    [line.quantity * ln.price_unit for ln in lines])
            invoice.goods_free_amount_total = goods_free_amount_total
