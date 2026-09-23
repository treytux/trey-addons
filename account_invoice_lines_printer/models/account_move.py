###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models
from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = 'account.move'

    print_line = fields.Boolean(
        string='Print alternative lines?'
    )
    print_line_untaxed = fields.Float(
        string='Print Lines Untaxed Amount',
        compute='_compute_print_line_totals',
    )
    print_line_tax = fields.Float(
        string='Print Lines Tax',
        compute='_compute_print_line_totals',
    )
    print_line_total = fields.Float(
        string='Print Lines Total',
        compute='_compute_print_line_totals',
    )
    print_line_ids = fields.One2many(
        comodel_name='account.move.print.line',
        inverse_name='move_id',
        string='Print Lines',
    )

    @api.depends('print_line_ids.price_subtotal', 'print_line_ids.price_total')
    def _compute_print_line_totals(self):
        for move in self:
            move.print_line_untaxed = sum(
                move.print_line_ids.mapped('price_subtotal'))
            move.print_line_total = sum(
                move.print_line_ids.mapped('price_total'))
            move.print_line_tax = (
                move.print_line_total - move.print_line_untaxed)

    def button_diff_update(self):
        self._compute_print_line_totals()

    def action_print_line_copy(self):
        for move in self:
            move.print_line_ids.unlink()
            product_lines = move.invoice_line_ids.filtered(
                lambda line: line.display_type == 'product')
            for line in product_lines:
                self.env['account.move.print.line'].create({
                    'move_id': move.id,
                    'name': line.name,
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'tax_ids': [(6, 0, line.tax_ids.ids)],
                })

    def check_print_lines(self):
        def msg(field):
            return _(
                'You can\'t activate print lines. The original %s and the '
                '%s of the lines to print must match') % (field, field)
        for move in self:
            if float_compare(
                    move.amount_total, move.print_line_total,
                    precision_digits=2):
                raise exceptions.UserError(msg('total'))
            if float_compare(
                    move.amount_tax, move.print_line_tax,
                    precision_digits=2):
                raise exceptions.UserError(msg('tax'))
            if float_compare(
                    move.amount_untaxed, move.print_line_untaxed,
                    precision_digits=2):
                raise exceptions.UserError(msg('untaxed'))

    @api.onchange('print_line')
    def _onchange_print_line(self):
        if self.print_line:
            self.check_print_lines()

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves.filtered('print_line').check_print_lines()
        return moves

    def write(self, vals):
        if vals.get('print_line'):
            self.check_print_lines()
        return super().write(vals)
