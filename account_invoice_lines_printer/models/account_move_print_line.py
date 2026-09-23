###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountMovePrintLine(models.Model):
    _name = 'account.move.print.line'
    _description = 'Invoice Print Line'

    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice',
        ondelete='cascade',
    )
    name = fields.Char(string='Description')
    quantity = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure',
    )
    price_unit = fields.Float(
        string='Unit Price',
        digits='Product Price',
    )
    discount = fields.Float(string='Disc.%')
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='account_move_print_line_tax_rel',
        column1='print_line_id',
        column2='tax_id',
        string='Taxes',
    )
    price_subtotal = fields.Float(
        string='Untaxed Amount',
        compute='_compute_amounts',
    )
    price_total = fields.Float(
        string='Total',
        compute='_compute_amounts',
    )

    @api.depends('quantity', 'price_unit', 'discount', 'tax_ids')
    def _compute_amounts(self):
        for line in self:
            price_unit = line.price_unit * (1 - (line.discount or 0) / 100)
            taxes = line.tax_ids.compute_all(
                price_unit, currency=line.move_id.currency_id,
                quantity=line.quantity, partner=line.move_id.partner_id)
            line.price_subtotal = taxes['total_excluded']
            line.price_total = taxes['total_included']
