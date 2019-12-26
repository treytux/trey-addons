# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    booking_id = fields.Many2one(
        comodel_name='booking',
        string='Booking',
        ondelete='restrict',
        copy=True)

    @api.multi
    def action_cancel_draft(self):
        for invoice in self:
            if not invoice.booking_id:
                continue
            if invoice.type in ('out_invoice', 'out_refund'):
                invoice.booking_id.invoiced = False
            elif invoice.type in ('in_invoice', 'in_refund'):
                for line in invoice.invoice_line:
                    line.booking_line_id.invoiced = False
        return super(AccountInvoice, self).action_cancel_draft()

    @api.multi
    def invoice_validate(self):
        for invoice in self:
            if not invoice.booking_id:
                continue
            if invoice.type in ('out_invoice', 'out_refund'):
                invoice.booking_id.invoiced = True
            elif invoice.type in ('in_invoice', 'in_refund'):
                for line in invoice.invoice_line:
                    line.booking_line_id.invoiced = True
        return super(AccountInvoice, self).invoice_validate()

    @api.multi
    def unlink(self):
        for invoice in self:
            if not invoice.booking_id:
                continue
            if invoice.type in ('out_invoice', 'out_refund'):
                invoice.booking_id.invoiced = False
            elif invoice.type in ('in_invoice', 'in_refund'):
                for line in invoice.invoice_line:
                    line.booking_line_id.invoiced = False
        return super(AccountInvoice, self).unlink()

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None,
                        description=None, journal_id=None):
        values = super(AccountInvoice, self)._prepare_refund(
            invoice, date=date, period_id=period_id,
            description=description, journal_id=journal_id)
        values['booking_id'] = (
            invoice.booking_id and invoice.booking_id.id or None)
        return values


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    booking_line_id = fields.Many2one(
        comodel_name='booking.line',
        string='Booking Line',
        copy=True)
