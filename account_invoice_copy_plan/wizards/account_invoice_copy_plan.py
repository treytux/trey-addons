###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import _, exceptions, fields, models


class AccountInvoiceCopyPlan(models.TransientModel):
    _name = 'account.invoice.copy_plan'
    _description = 'Wizard for copy invoice with a plan'

    period = fields.Selection(
        selection=[
            ('day', 'Days'),
            ('month', 'Months'),
            ('Year', 'Year'),
        ],
        string='Period',
        default='month',
        required=True,
    )
    quantity = fields.Integer(
        string='Quantity',
        required=True,
    )

    def _copy_invoice(self, invoice):
        date = invoice.date_invoice
        invoices = self.env['account.invoice']
        for index in range(1, self.quantity + 1):
            if self.period == 'day':
                new_date = date + relativedelta(day=index)
            elif self.period == 'month':
                new_date = date + relativedelta(months=index)
            elif self.period == 'month':
                new_date = date + relativedelta(years=index)
            invoices |= invoice.copy({'date_invoice': new_date})
        return invoices

    def create_invoices(self):
        assert self._context.get('active_ids'), 'Missing active_ids'
        invoices = self.env['account.invoice'].browse(
            self._context['active_ids'])
        invoices_without_date = invoices.filtered(lambda i: not i.date_invoice)
        if invoices_without_date:
            raise exceptions.UserError(
                _('Invoices ID %s don\'t has date') % (
                    invoices_without_date.ids))
        created_invoices = self.env['account.invoice']
        for invoice in invoices:
            created_invoices |= self._copy_invoice(invoice)
        return created_invoices
