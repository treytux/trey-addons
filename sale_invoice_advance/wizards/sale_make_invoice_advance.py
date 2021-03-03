###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    percents = fields.Char(
        string='Advance percents',
        help='You can indicate one or more percentages separated by +',
    )
    advance_payment_method = fields.Selection(
        selection_add=[
            ('advance', 'Advance (percents)'),
        ],
    )

    @api.onchange('percents')
    def onchange_advance_payment_method(self):
        if self.advance_payment_method != 'advance':
            return
        self._get_percent_values()

    def _get_percent_values(self):
        percents = self.percents.replace(' ', '').replace(',', '.').split('+')
        try:
            vals = [round(float(v), 2) for v in percents if v]
        except Exception:
            raise UserError(_(
                'You must enter valid numerical values separated by + sign'))
        if sum(vals) >= 100:
            raise UserError(_(
                'The sum of the percentages is equal or greater than 100%'))
        return vals

    @api.multi
    def create_invoices(self):
        if self.advance_payment_method != 'advance':
            return super().create_invoices()
        if not self.amount:
            self.amount = 50
        percent = sum(self._get_percent_values())
        sales = self.env['sale.order'].browse(
            self._context.get('active_ids', []))
        for sale in sales:
            if percent + sale.percent_advanced >= 100:
                raise UserError(_(
                    'Order %s has advanced %s%% and you try to advance '
                    'another %s%%, it is not possible to advance more than '
                    '100%%' % (sale.name, sale.percent_advanced, percent)))
        return super().create_invoices()

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        invoice = super()._create_invoice(order, so_line, amount)
        if self.advance_payment_method != 'advance':
            return invoice
        invoices = self.env['account.invoice']
        for (index, percent) in enumerate(self._get_percent_values()):
            invoices |= self._create_advance_invoice(
                order, so_line, invoice, percent, index + 1)
        invoice.unlink()
        return invoices

    def _create_advance_invoice(self, order, so_line, invoice2copy, percent,
                                index):
        amount = order.amount_untaxed * percent / 100
        line = so_line.copy({
            'order_id': so_line.order_id.id,
            'price_unit': amount,
            'name': _('Advance %.2f%%') % percent,
        })
        invoice = invoice2copy.copy({
            'date_invoice': fields.Date.today() + relativedelta(months=index),
        })
        invoice.invoice_line_ids[0].write({
            'price_unit': amount,
            'sale_line_ids': [(6, 0, [line.id])],
            'name': _('Advance %.2f%% of %s') % (
                percent, order.client_order_ref or order.name),
        })
        invoice.compute_taxes()
        invoice.message_post_with_view(
            'mail.message_origin_link',
            values={'self': invoice, 'origin': order},
            subtype_id=self.env.ref('mail.mt_note').id)
        return invoice
