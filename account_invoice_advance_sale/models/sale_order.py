###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    account_invoice_advance_sale_method = fields.Selection(
        related='company_id.account_invoice_advance_sale_method',
    )
    advance_formula = fields.Char(
        string='Advance percents',
        help='You can indicate one or more percentages separated by +')
    advance_line_ids = fields.One2many(
        comodel_name='sale.order.advance_line',
        inverse_name='sale_id',
        string='Advance lines',
    )

    def get_advance_percents(self):
        self.ensure_one()
        try:
            if self.advance_line_ids:
                return self.advance_line_ids.mapped('percent')
            if not self.advance_formula:
                return []
            formula = self.advance_formula.replace(' ', '').replace(',', '.')
            return [round(float(v), 2) for v in formula.split('+') if v]
        except Exception:
            raise ValidationError(_(
                'Advance percents "%s" is incorrect.\nRemember, set a number '
                'or numbers separated by +') % self.advance_formula)

    @api.constrains('advance_formula')
    def _check_advance_formula(self):
        for sale in self:
            percents = sale.get_advance_percents()
            if sum(percents) > 100:
                raise ValidationError(_(
                    'The sum of the advances percentages cannot be greater '
                    'than 100%'))

    def _finalize_invoices(self, invoices, references):
        wizard_obj = self.env['account.invoice.make_advance']
        super()._finalize_invoices(invoices, references)
        for invoice, sales in references.items():
            percents = [
                '+'.join([str(v) for v in s.get_advance_percents() if v])
                for s in sales]
            if len(set(percents)) != 1:
                continue
            sale = sales[0]
            percents = sale.get_advance_percents()
            invs = wizard_obj._create_advance_invoice(
                invoice, percents[:-1] if sum(percents) == 100 else percents)
            if not sale.advance_line_ids:
                continue
            for index, inv in enumerate(invs[1:]):
                sale.advance_line_ids[index].apply_invoice(inv)
            if len(invs) == len(percents):
                sale.advance_line_ids[len(percents) - 1].apply_invoice(invs[0])

    def _get_invoiced(self):
        super()._get_invoiced()
        for sale in self:
            sale.invoice_ids |= sale.mapped('invoice_ids.advance_invoice_ids')
            sale.invoice_count = len(sale.invoice_ids)
