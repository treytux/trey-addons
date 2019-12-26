# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _


class BookingCustomerInvoice(models.TransientModel):
    _inherit = 'booking.customer.invoice'

    @api.multi
    def create_invoice(self):
        active_ids = self.env.context['active_ids']
        account_obj = self.env['account.invoice']
        account_line_obj = self.env['account.invoice.line']
        bookings = self.env['booking'].browse(active_ids)
        for booking in bookings:
            if booking.invoiced:
                continue
            company_currency_id = self.env.user.company_id.currency_id
            if booking.currency_id.id == company_currency_id.id:
                change_factor = 1
            else:
                context = self.env.context.copy()
                context['date'] = booking.date
                change_factor = booking.currency_id.with_context(
                    context)._get_conversion_rate(
                        to_currency=company_currency_id,
                        from_currency=booking.currency_id)
            date = self.invoice_date and self.invoice_date or booking.date_end
            partner_id = booking.agency_id
            if not partner_id.property_account_receivable:
                raise exceptions.Warning(
                    _('%s have not receivable account define. '
                        'Please, go to partner and assign it one')
                    % booking.agency_id.name)
            company_product_booking = self.env.user.company_id.product_id
            if (not company_product_booking or not
                    company_product_booking.property_account_income):
                raise exceptions.Warning(
                    _('Please, go to company settings, add a product and '
                      'assign it one receivable account'))
            invoice_id = account_obj.create({
                'journal_id': self.journal_id.id,
                'currency_id': booking.currency_id.id,
                'date_invoice': date,
                'partner_id': partner_id.id,
                'origin': booking.name,
                'name': booking.name,
                'type': 'out_invoice',
                'fiscal_position': partner_id.property_account_position.id,
                'booking_id': booking.id,
                'booking_net_price': booking.booking_net_price,
                'account_id': partner_id.property_account_receivable.id,
                'currency_rate': change_factor,
            })
            accin = company_product_booking.property_account_income
            for line in booking.booking_line:
                account_line_obj.create({
                    'account_id': accin.id,
                    'product_id': company_product_booking.id,
                    'quantity': 1,
                    'uos_id': company_product_booking.uom_id.id,
                    'invoice_id': invoice_id.id,
                    'name': booking.name,
                    'booking_line_id': booking.booking_line[0].id,
                    'price_unit': booking.amount_selling,
                    'commission_amount': line.commission_amount,
                    'commission_tax_id': (line.commission_tax_id and
                                          line.commission_tax_id.id or None),
                    'agents': [(0, 0, {
                        'agent': agent.agent.id,
                        'commission': agent.commission.id,
                        'amount': agent.amount}) for agent in line.agents
                    ]})
            booking.write({'state': 'done'})
