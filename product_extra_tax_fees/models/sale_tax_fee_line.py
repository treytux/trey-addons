###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleTaxFeeLine(models.Model):
    _inherit = 'account.tax.fee.line'
    _name = 'sale.tax.fee.line'
    _description = 'Sale tax fee line'

    sale_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        ondelete='cascade',
        readonly=True,
    )
    sale_id = fields.Many2one(
        related='sale_line_id.order_id',
    )
    product_id = fields.Many2one(
        related='sale_line_id.product_id',
        string='Product',
    )
    partner_id = fields.Many2one(
        related='sale_line_id.order_id.partner_id',
        string='Partner',
    )
    state = fields.Selection(
        string='Status',
        related='sale_line_id.state',
    )

    @api.depends('product_id', 'partner_id')
    def _compute_tax_fee(self):
        for fee_line in self:
            if not fee_line.tax_fee_id:
                fee_line.tax_fee_amount = 0
                continue
            fee_line.tax_fee_amount = fee_line.tax_fee_id.get_tax_fee(
                fee_line, fee_line.sale_line_id.product_uom_qty)
