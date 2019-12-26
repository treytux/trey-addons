# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class BookingSupplierInvoice(models.TransientModel):
    _name = 'booking.supplier.invoice'
    _description = "Booking Supplier Invoice"

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Destination Journal',
        domain='[("type", "=", "purchase")]',
        required=True)
    invoice_date = fields.Date(
        string='Invoice Date')

    @api.multi
    def open_invoice(self):
        self.create_invoice()
        return True

    @api.multi
    def create_invoice(self):
        active_ids = self.env.context['active_ids']
        lines = self.env['booking.line'].browse(active_ids)
        product = self.env.user.company_id.product_id
        if not product or not product.property_account_expense:
            raise exceptions.Warning(
                _('Please, assign a product and assign a product account in '
                  'company settings'))
        for line in lines:
            if line.invoiced or not line.supplier_id:
                continue
            company_currency = self.env.user.company_id.currency_id
            if line.cost_currency_id.id == company_currency.id:
                change_factor = 1
            else:
                context = self.env.context.copy()
                context['date'] = line.date
                change_factor = line.cost_currency_id.with_context(
                    context)._get_conversion_rate(
                        from_currency=line.cost_currency_id,
                        to_currency=company_currency)
            date = self.invoice_date or line.date_end
            if not line.supplier_id.property_account_payable:
                raise exceptions.Warning(
                    _('%s have not receivable account define. '
                        'Please, go to supplier and assign it one')
                    % line.supplier_id.name)
            invoice = self.env['account.invoice'].create({
                'journal_id': self.journal_id.id,
                'currency_id': line.cost_currency_id.id,
                'date_invoice': date,
                'partner_id': line.supplier_id.id,
                'origin': line.ex_reference,
                'name': line.booking_code,
                'reference': line.booking_code,
                'type': 'in_invoice',
                'fiscal_position':
                    line.supplier_id.property_account_position and
                    line.supplier_id.property_account_position.id or None,
                'booking_id': line.booking_id.id,
                'account_id': line.supplier_id.property_account_payable.id,
                'currency_rate': change_factor,
                'reference_type': 'none',
                'supplier_invoice_number':
                    line.supplier_invoice_number or line.ex_reference or
                    line.booking_id.name})
            self.env['account.invoice.line'].create({
                'account_id': product.property_account_expense.id,
                'product_id': product.id,
                'quantity': 1,
                'uos_id': product.uom_id.id,
                'invoice_id': invoice.id,
                'name': '%s-%s' % (line.booking_code, line.name),
                'price_unit': line.cost_net,
                'booking_line_id': line.id})
            invoice.check_total = invoice.amount_total
            line.invoiced = True
