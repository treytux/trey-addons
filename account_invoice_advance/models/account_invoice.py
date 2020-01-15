###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    advance_invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        compute='_compute_advanced',
        string='Advance of invoice',
    )
    advance_invoice_ids = fields.One2many(
        comodel_name='account.invoice',
        compute='_compute_advanced',
        string='Advances invoices',
    )
    advance_invoice_count = fields.Float(
        compute='_compute_advanced',
        string='Advances',
    )
    amount_advanced = fields.Float(
        string='Advanced',
        help='Total amount advanced without taxes',
        compute='_compute_advanced',
    )
    percent_advanced = fields.Float(
        string='Advanced (%)',
        compute='_compute_advanced',
    )

    @api.depends('invoice_line_ids')
    def _compute_advanced(self):
        for invoice in self:
            amount_untaxed = sum(invoice.invoice_line_ids.filtered(
                lambda l: not l.advance_line_id).mapped('price_subtotal'))
            lines = invoice.invoice_line_ids.filtered(
                lambda l: l.advance_line_id)
            invoice.amount_advanced = sum(lines.mapped('price_unit')) * -1
            invoice.percent_advanced = 0
            if invoice.amount_advanced:
                invoice.percent_advanced = round(
                    invoice.amount_advanced * 100 / amount_untaxed, 2)
            invoice.advance_invoice_ids = [
                (6, 0, lines.mapped('advance_line_id.invoice_id').ids)]
            invoice.advance_invoice_count = len(invoice.advance_invoice_ids)
            invoice.advance_invoice_id = invoice.mapped(
                'invoice_line_ids.advance_line_ids.invoice_id')

    @api.multi
    def copy_data(self, default=None):
        if default is None:
            default = {}
        if 'invoice_line_ids' in default:
            return super().copy_data(default)
        lines = self.invoice_line_ids.filtered(lambda l: not l.advance_line_id)
        default['invoice_line_ids'] = [(0, 0, l.copy_data()[0]) for l in lines]
        return super().copy_data(default)

    @api.multi
    def action_view_advance_invoices(self):
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if self.advance_invoice_count > 1:
            action['domain'] = [('id', 'in', self.advance_invoice_ids.ids)]
        elif self.advance_invoice_count == 1:
            form_view = [(self.env.ref('account.invoice_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view) for state, view in action['views']
                    if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = self.advance_invoice_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def unlink(self):
        for invoice in self:
            advance_lines = invoice.invoice_line_ids.filtered(
                lambda l: l.advance_line_ids)
            advance_lines.unlink()
            advance_states = invoice.mapped('advance_invoice_ids.state')
            if not all([s == 'draft' for s in advance_states]):
                raise UserError(_(
                    'Not is possible remove an invoice with advances that not '
                    'is in draft state'))
            invoice.advance_invoice_ids.unlink()
        super().unlink()
