# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _


class BookingCustomerInvoice(models.TransientModel):
    _inherit = 'booking.customer.invoice'

    @api.multi
    def create_invoice(self):
        res = super(BookingCustomerInvoice, self).create_invoice()
        active_ids = self.env.context['active_ids']
        bookings = self.env['booking'].browse(active_ids)
        for booking in bookings:
            if booking.methabook_id == 0 or booking.date_init <= '2018-12-31':
                continue
            if not booking.booking_line.service_country_id:
                raise exceptions.Warning(
                    _('Not Service Country defined in Booking:%s') %
                    booking.name)
            if not booking.booking_line.service_country_id.intrastat:
                continue
            booking_tax = self.env.user.company_id.tax_product_id
            if not booking_tax or not booking_tax.property_account_income or\
                    not booking_tax.taxes_id:
                raise exceptions.Warning(
                    _('Please, go to company settings and add a product for '
                      'tax and assign receivable account, taxes, etc'))
            invoice = booking.invoices.filtered(
                lambda i: i.type == 'out_invoice' and i.state == 'draft')
            inv_booking_line = invoice.invoice_line[0]
            inv_booking_line.write({'price_unit': booking.amount_cost_net})
            self.env['account.invoice.line'].create({
                'account_id': booking_tax.property_account_income.id,
                'product_id': booking_tax.id,
                'quantity': 1,
                'uos_id': booking_tax.uom_id.id,
                'invoice_id': invoice.id,
                'name': booking.name,
                'booking_line_id': booking.booking_line[0].id,
                'price_unit': booking.amount_selling - booking.amount_cost_net,
                'invoice_line_tax_id': [(6, 0, [booking_tax.taxes_id.id])]})
            invoice.button_reset_taxes()
        return res
