# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _, exceptions


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def confirm_paid(self):
        for invoice in self:
            if not invoice.booking_id or not (
                    invoice.booking_id.methabook_id != 0):
                continue
            if invoice.booking_id and invoice.type == 'out_invoice':
                # Informa vía api del pago de la reserva.
                # Api iboosy solo recive peticiones de la IP del contenedor.
                paid_ok = self.env[
                    'booking.webservice'].mt_send_booking_as_paid(
                    invoice.booking_id)
                if not paid_ok:
                    raise exceptions.Warning(
                        _('Error connecting to booking platform to confirm '
                          'pay bookings, please retry'))
                if paid_ok and invoice.booking_id.state != 'done':
                    invoice.booking_id.state = 'paid'
            if invoice.booking_id and invoice.type == 'in_invoice':
                invoice.booking_id.state = 'done'
        return super(AccountInvoice, self).confirm_paid()

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        for invoice in self:
            if invoice.booking_id and invoice.type == 'out_invoice':
                invoice.booking_id.invoiced = False
        return res

    @api.multi
    def action_cancel_draft(self):
        for invoice in self:
            if invoice.booking_id and invoice.type == 'out_invoice':
                if len(invoice.booking_id.invoices) > 1:
                    no_cancelled_invoice = False
                    for inv in invoice.booking_id.invoices:
                        if inv.state != 'cancel' and inv.type == 'out_invoice':
                            no_cancelled_invoice = True
                            break
                    if no_cancelled_invoice:
                        raise exceptions.Warning(
                            _('Booking %s already has a non cancelled'
                              'associated invoice.'
                                % invoice.booking_id.name))
                invoice.booking_id.invoiced = True
        res = super(AccountInvoice, self).action_cancel_draft()
        return res
