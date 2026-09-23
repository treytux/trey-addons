###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    global_discount_ids = fields.Many2many(
        comodel_name='res.partner.global_discount',
        relation='res_partner_global_discount2account_invoice_rel',
        column1='invoice_id',
        column2='discount_id',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    amount_untaxed_before_discount = fields.Monetary(
        compute='_compute_amount_untaxed_before_discount',
        store=True,
        string='Untaxed Amount Before Discount',
        help='''Summation of untaxed amount subtotals of lines with unmodified
        global discounts before these be applied''',
    )
    amount_discount_untaxed = fields.Monetary(
        compute='_compute_amount_untaxed_before_discount',
        store=True,
        string='Untaxed Discount Amount',
    )

    @api.depends(
        'invoice_line_ids', 'global_discount_ids', 'invoice_line_ids.discount',
        'invoice_line_ids.price_unit', 'invoice_line_ids.quantity')
    def _compute_amount_untaxed_before_discount(self):
        for invoice in self:
            invoice.amount_untaxed_before_discount = sum(
                [ln.price_unit * ln.quantity for ln in invoice.invoice_line_ids])
            invoice.amount_discount_untaxed = sum(
                [ln.price_subtotal for ln in invoice.invoice_line_ids]) - (
                invoice.amount_untaxed_before_discount)

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        if not self.partner_id:
            return res
        self.global_discount_ids = [
            (6, 0, self.partner_id.global_discount_ids.ids)]
