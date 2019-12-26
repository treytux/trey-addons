# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
import logging

_log = logging.getLogger(__name__)


class MassiveInvoice(models.TransientModel):
    _name = 'booking.massive.invoice'
    _description = "Booking Massive Invoice"

    init_date = fields.Date(
        string="Date Init",
        help='Begin Travel')
    end_date = fields.Date(
        string="Date End",
        help='End Travel')

    @api.one
    def massive_invoice_booking(self):
        # Seleccionar reservas con estado pagado e importe pendiente 0
        # ademas de que su fecha de salida de servicio sea inferior a hoy
        # dt = fields.Date.from_string(fields.Date.today())
        services = self.env['booking'].search([
            ('state', 'in', ('paid', 'confirmed')),
            ('date_end', '>=', self.init_date),
            ('date_end', '<=', self.end_date), ('invoiced', '=', False)])
        for booking in services:
            if booking.invoiced:
                _log.info(
                    'Booking "%s" already invoiced: %s' % (
                        booking.name,
                        ', '.join([
                            i.number and i.number or 'ID: %s' % i.id
                            for i in booking.invoices])))
                continue
            invoice_ids = []
            # Buscar diarios de factura y cobro por divisa
            journal = self.env.user.company_id.journal_ids.filtered(
                lambda x: x.currency_id.id == booking.currency_id.id)
            if not journal:
                journal = self.env.user.company_id.journal_ids.filtered(
                    lambda x: x.default is True)
            invoice_journal_id = journal.invoice_journal_id
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
            values = {
                'journal_id': invoice_journal_id.id,
                'currency_id': booking.currency_id.id,
                'date_invoice': booking.date_end,
                'partner_id': booking.agency_id.id,
                'origin': booking.name,
                'name': booking.name,
                'type': 'out_invoice',
                'fiscal_position':
                    booking.agency_id.property_account_position.id,
                'booking_id': booking.id,
                'account_id': booking.agency_id.property_account_receivable.id,
                'currency_rate': change_factor
            }
            invoice_id = self.env['account.invoice'].create(values)
            product_id = self.env.user.company_id.product_id
            line_values = {
                'account_id': product_id.property_account_income.id,
                'product_id': product_id.id,
                'quantity': 1,
                'uos_id': product_id.uom_id.id,
                'invoice_id': invoice_id.id,
                'name': booking.name,
                'price_unit': booking.amount_selling
            }
            self.env['account.invoice.line'].create(line_values)
            booking.write({'invoiced': True, 'state': 'done'})
            invoice_ids.append(invoice_id)
            _log.info('=' * 79)
            _log.info('Create invoice "%s from booking "%s"' % (
                invoice_id.name, booking.name))
            # Recalcular factura
            invoice_id.button_compute()
            # Aceptar factura
            invoice_id.action_date_assign()
            invoice_id.action_move_create()
            invoice_id.action_number()
            invoice_id.invoice_validate()
            _log.info('Invoice Confirm number:"%s"' % invoice_id.number)

            # TODO: Pago de la factura

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def run_massive_invoice_booking(self):
        # Update booking at the given frequency
        dt = fields.Date.today()
        services = self.env['booking'].search([
            ('state', 'in', ('paid', 'confirmed')), ('date_end', '<', dt),
            ('invoiced', '=', False)])
        self.with_context(cron=True).massive_invoice_booking(services)

    @api.model
    def _run_massive_invoice_booking(self):
        _log.info('=' * 79)
        _log.info('Starting Invoice Booking update cron')
        _log.info('=' * 79)
        self.run_invoice_booking()
        _log.info('=' * 79)
        _log.info('End Invoice Booking update cron')
        _log.info('=' * 79)
