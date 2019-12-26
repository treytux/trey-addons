# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class BookingCustomerInvoice(models.TransientModel):
    _name = 'booking.customer.invoice'
    _description = "Booking Customer Invoice"

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string="Destination Journal",
        domain='[("type", "=", "sale")]',
        required=True)
    invoice_date = fields.Date(
        string='Invoice Date')
    booking_date = fields.Boolean(
        string='Using Booking Date?')

    @api.multi
    def open_invoice(self):
        self.create_invoice()
        return True

    @api.multi
    def create_invoice(self):
        active_ids = self.env.context['active_ids']
        bookings = self.env['booking'].browse(active_ids)
        product = self.env.user.company_id.product_id
        if not product or not product.property_account_income:
            raise exceptions.Warning(
                _('Please, assign a product and assign a product account in '
                  'company settings'))
        for booking in bookings:
            if booking.invoiced:
                continue
            company_currency = self.env.user.company_id.currency_id
            if booking.currency_id.id == company_currency.id:
                change_factor = 1
            else:
                context = self.env.context.copy()
                context['date'] = booking.date
                change_factor = booking.currency_id.with_context(
                    context)._get_conversion_rate(
                        to_currency=company_currency,
                        from_currency=booking.currency_id)
            date = self.invoice_date and self.invoice_date or booking.date_end
            partner_id = booking.agency_id
            if not partner_id.property_account_receivable:
                raise exceptions.Warning(
                    _('%s have not receivable account define. '
                        'Please, go to partner and assign it one')
                    % booking.agency_id.name)
            invoice = self.env['account.invoice'].create({
                'journal_id': self.journal_id.id,
                'currency_id': booking.currency_id.id,
                'date_invoice': date,
                'partner_id': partner_id.id,
                'origin': booking.name,
                'name': booking.name,
                'type': 'out_invoice',
                'fiscal_position':
                    partner_id.property_account_position and
                    partner_id.property_account_position.id or None,
                'booking_id': booking.id,
                'account_id': partner_id.property_account_receivable.id,
                'currency_rate': change_factor})
            self.env['account.invoice.line'].create({
                'account_id': product.property_account_income.id,
                'product_id': product.id,
                'quantity': 1,
                'uos_id': product.uom_id.id,
                'invoice_id': invoice.id,
                'name': booking.name,
                'booking_line_id': booking.booking_line[0].id,
                'price_unit': booking.amount_selling})
            booking.write({'state': 'done', 'invoiced': True})
