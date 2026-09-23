###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountTaxFeeLine(models.Model):
    _name = 'account.tax.fee.line'
    _description = 'Account tax fee line'
    _rec_name = 'tax_fee_id'

    invoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        ondelete='cascade',
        readonly=True,
    )
    invoice_id = fields.Many2one(
        related='invoice_line_id.invoice_id',
    )
    product_id = fields.Many2one(
        related='invoice_line_id.product_id',
        string='Product',
    )
    partner_id = fields.Many2one(
        related='invoice_line_id.partner_id',
        string='Partner',
    )
    tax_fee_id = fields.Many2one(
        comodel_name='account.tax.fee',
        string='Tax fee',
        readonly=True,
    )
    tax_fee_amount = fields.Float(
        string='Amount',
        compute='_compute_tax_fee',
    )
    state = fields.Selection(
        string='Status',
        related='invoice_line_id.invoice_id.state',
    )

    @api.model
    def _get_formula_input_dict(self, tax_fee):
        return {
            'tax_fee': tax_fee,
            'self': self,
            'product_id': self.product_id,
        }

    @api.depends('product_id', 'partner_id')
    def _compute_tax_fee(self):
        for fee_line in self:
            if not fee_line.tax_fee_id:
                fee_line.tax_fee_amount = 0
                continue
            fee_line.tax_fee_amount = fee_line.tax_fee_id.get_tax_fee(
                fee_line, fee_line.invoice_line_id.quantity)
