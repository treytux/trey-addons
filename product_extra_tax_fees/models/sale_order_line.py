###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    tax_fee_amount = fields.Float(
        string='Tax fee amount',
        compute='_compute_tax_fee_amount',
        store=True,
    )
    tax_fee_ids = fields.One2many(
        comodel_name='sale.tax.fee.line',
        inverse_name='sale_line_id',
        string='Tax fees',
        compute='_compute_tax_fees',
        store=True,
    )

    @api.depends('product_id', 'order_id.partner_id', 'product_uom_qty')
    def _compute_tax_fees(self):
        for sale_line in self:
            sale_line.tax_fee_ids = False
            if not sale_line.product_id:
                continue
            tax_fees = sale_line.product_id.product_tmpl_id.get_tax_fees(
                sale_line.order_id.partner_id)
            sale_line.tax_fee_ids = (tax_fees and [
                (0, 0, {'tax_fee_id': f.id}) for f in tax_fees] or False)

    @api.depends('tax_fee_ids')
    def _compute_tax_fee_amount(self):
        for sale_line in self:
            sale_line.tax_fee_amount = sum(
                sale_line.tax_fee_ids.mapped('tax_fee_amount'))
