###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountInvoiceMakeAdvance(models.TransientModel):
    _name = 'account.invoice.make_advance'
    _description = 'Make advance of invoices'

    formula = fields.Char(
        string='Advance percents',
        help='You can indicate one or more percentages separated by +')

    def _get_percent_values(self):
        formula = self.formula.replace(' ', '').replace(',', '.').split('+')
        try:
            vals = [round(float(v), 2) for v in formula if v]
        except Exception:
            raise UserError(_(
                'You must enter valid numerical values separated by + sign'))
        if sum(vals) >= 100:
            raise UserError(_(
                'The sum of the percentages is equal or greater than 100%'))
        return vals

    @api.multi
    def action_view_invoice(self):
        invoices = self.env['account.invoice'].browse(
            self._context.get('active_ids', []))
        invoices = invoices.mapped('advance_invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.invoice_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view) for state, view in action['views']
                    if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def create_advance_invoices(self):
        invoices = self.env['account.invoice'].browse(
            self._context.get('active_ids', []))
        if ['draft'] != list(set(invoices.mapped('state'))):
            raise UserError(_('Only draft invoices for create advances'))
        percents = self._get_percent_values()
        for invoice in invoices:
            self._create_advance_invoice(invoice, percents)
        if self._context.get('open_invoices', False):
            return self.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def _create_advance_invoice(self, invoice, percents):
        if sum(percents) + invoice.percent_advanced >= 100:
            raise UserError(_(
                'The invoice %s has a advance percent %s%% with the new '
                'advances the percents sum %s%% that is greate or equal than '
                '100%%. Not is possible advance 100%% or more than one '
                'invoice' % (
                    invoice.number or invoice.name, invoice.percent_advanced,
                    sum(percents))))
        product = self.env.ref('account_invoice_advance.advance_product')
        amount = invoice.amount_untaxed + invoice.amount_advanced
        invoices = self.env['account.invoice']
        invoices |= invoice
        for percent in percents:
            price_unit = amount * percent / 100
            new_invoice = invoice.copy({
                'name': self._get_invoice_name(invoice, percent),
                'invoice_line_ids': False,
            })
            advance_line = self._create_invoice_line(
                new_invoice, product, price_unit, percent)
            new_invoice.compute_taxes()
            self._create_invoice_line(
                invoice, product, price_unit * -1, percent, advance_line)
            invoices |= new_invoice
        invoice.compute_taxes()
        return invoices

    @api.multi
    def _create_invoice_line(self, invoice, product, price_unit, percent,
                             advance_line=False):
        line_obj = self.env['account.invoice.line'].with_context(
            force_company=invoice.company_id.id)
        line = line_obj.new({
            'sequence': 99999999,
            'invoice_id': invoice.id,
            'advance_line_id': advance_line.id if advance_line else False,
            'product_id': product.id,
            'quantity': 1,
        })
        line._onchange_product_id()
        line.update({
            'name': self._get_invoice_name(invoice, percent),
            'price_unit': price_unit,
        })
        return line_obj.create(line._convert_to_write(line._cache))

    @api.multi
    def _get_invoice_name(self, invoice, percent):
        name = _('Advance {0:.0f}%').format(percent)
        if invoice.origin:
            name += _(' of %s') % invoice.origin
        return name
