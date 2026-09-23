###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    tax_fee_amount = fields.Float(
        string='Tax fee amount',
        compute='_compute_tax_fee_amount',
        store=True,
    )
    tax_fee_ids = fields.One2many(
        comodel_name='account.tax.fee.line',
        inverse_name='invoice_line_id',
        string='Tax fees',
        compute='_compute_tax_fees',
        store=True,
    )

    @api.depends('product_id', 'partner_id', 'quantity')
    def _compute_tax_fees(self):
        for inv_line in self:
            inv_line.tax_fee_ids = False
            if not inv_line.product_id:
                continue
            tax_fees = inv_line.product_id.product_tmpl_id.get_tax_fees(
                inv_line.partner_id)
            inv_line.tax_fee_ids = (tax_fees and [
                (0, 0, {'tax_fee_id': f.id}) for f in tax_fees] or False)

    @api.depends('tax_fee_ids')
    def _compute_tax_fee_amount(self):
        for inv_line in self:
            inv_line.tax_fee_amount = sum(
                inv_line.tax_fee_ids.mapped('tax_fee_amount'))
