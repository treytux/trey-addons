###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    global_discount_ids = fields.Many2many(
        comodel_name='res.partner.global_discount',
        relation='res_partner_global_discount2sale_rel',
        column1='sale_id',
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
        'order_line', 'global_discount_ids', 'order_line.discount',
        'order_line.price_unit', 'order_line.product_uom_qty')
    def _compute_amount_untaxed_before_discount(self):
        for sale in self:
            sale.amount_untaxed_before_discount = sum(
                [ln.price_unit * ln.product_uom_qty for ln in sale.order_line])
            sale.amount_discount_untaxed = sum(
                [ln.price_subtotal for ln in sale.order_line]) - (
                sale.amount_untaxed_before_discount)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(). onchange_partner_id()
        if not self.partner_id:
            return res
        self.global_discount_ids = [
            (6, 0, self.partner_id.global_discount_ids.ids)]
