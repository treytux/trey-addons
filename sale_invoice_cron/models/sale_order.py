###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime
import logging

from dateutil import relativedelta
from odoo import api, models

_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def cron_invoice_sales_filtered(self, invoice_date):
        date_field = (
            'effective_date' in self._fields
            and 'effective_date'
            or 'confirmation_date'
        )

        def filter(sale):
            date = sale[date_field]
            if not date:
                return True
            if isinstance(date, datetime.datetime):
                date = sale[date_field].date()
            return date <= invoice_date

        return self.filtered(filter)

    @api.model
    def _cron_get_invoice_date(self, day=None, months=0, today=None):
        if not day:
            day = datetime.date.today().day
        if not today:
            today = datetime.datetime.today().date()
        if isinstance(today, datetime.datetime):
            today = today.date()
        return today + relativedelta.relativedelta(months=months, day=day)

    @api.model
    def cron_invoice_sales(self, day=None, months=0):
        invoice_date = self._cron_get_invoice_date(day=day, months=months)
        _log.info('Invoice sales orders until %s' % invoice_date)
        sales = self.search([('invoice_status', '=', 'to invoice')])
        sales = sales.cron_invoice_sales_filtered(invoice_date)
        if not sales:
            _log.info('No sales to invoice for %s' % invoice_date)
            return []
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sales.ids,
            'active_id': sales[0].id,
            'log_step_sales_create_invoice': len(sales),
            'open_invoices': True,
        }
        wizard = self.env['sale.advance.payment.inv'].with_context(ctx).create(
            {'advance_payment_method': 'all'})
        _log.info('Create invoice for %s sale orders' % len(sales))
        action = wizard.create_invoices()
        if action['res_id']:
            invoices = self.env['account.invoice'].browse(action['res_id'])
        else:
            invoices = self.env['account.invoice'].search(action['domain'])
        invoices.write({'date_invoice': invoice_date})
        _log.info('%s invoices created from %s sale orders' % (
            len(invoices), len(sales)))
        return invoices
