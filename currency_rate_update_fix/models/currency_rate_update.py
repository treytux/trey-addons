# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
###############################################################################
import logging

from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from openerp import models, fields, api, _
from openerp import exceptions

from ..services.currency_getter import Currency_getter_factory

_logger = logging.getLogger(__name__)

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'weeks': lambda interval: relativedelta(days=7 * interval),
    'months': lambda interval: relativedelta(months=interval),
}


class Currency_rate_update_service(models.Model):
    _inherit = 'currency.rate.update.service'

    @api.one
    def refresh_currency(self):
        _logger.info(
            'Starting to refresh currencies with service %s (company: %s)',
            self.service, self.company_id.name)
        factory = Currency_getter_factory()
        curr_obj = self.env['res.currency']
        rate_obj = self.env['res.currency.rate']
        company = self.company_id
        if company.auto_currency_up:
            main_currency = curr_obj.search([
                ('base', '=', True),
                ('company_id', '=', company.id)
            ], limit=1)
            if not main_currency:
                main_currency = curr_obj.search([
                    ('base', '=', True),
                    ('company_id', '=', False)
                ], limit=1)
            if not main_currency:
                raise exceptions.Warning(_('There is no base currency set!'))
            if main_currency.rate != 1:
                raise exceptions.Warning(_(
                    'Base currency rate should be 1.00!'))
            note = self.note or ''
            try:
                getter = factory.register(self.service)
                curr_to_fetch = map(lambda x: x.name, self.currency_to_update)
                res, log_info = getter.get_updated_currency(
                    curr_to_fetch,
                    main_currency.name,
                    self.max_delta_days
                )
                rate_name = \
                    fields.Datetime.to_string(datetime.utcnow().replace(
                        hour=0, minute=0, second=0, microsecond=0))
                for curr in self.currency_to_update:
                    if curr.id == main_currency.id:
                        continue
                    do_create = True
                    for rate in curr.rate_ids:
                        if rate.name == rate_name:
                            rate.rate = res[curr.name]
                            do_create = False
                            break
                    if do_create:
                        vals = {
                            'currency_id': curr.id,
                            'rate': res[curr.name],
                            'name': rate_name
                        }
                        rate_obj.create(vals)
                        _logger.info(
                            'Updated currency %s via service %s',
                            curr.name, self.service)
                msg = '%s \n%s currency updated. %s' % (
                    log_info or '',
                    fields.Datetime.to_string(datetime.today()),
                    note
                )
                self.write({'note': msg})
            except Exception as exc:
                error_msg = '\n%s ERROR : %s %s' % (
                    fields.Datetime.to_string(datetime.today()),
                    repr(exc),
                    note
                )
                _logger.error(repr(exc))
                self.write({'note': error_msg})
            if self._context.get('cron', False):
                midnight = time(0, 0)
                midnight_datetime = datetime.combine(
                    fields.Date.from_string(self.next_run), midnight)
                self.next_run = (
                    midnight_datetime + _intervalTypes[str(
                        self.interval_type)](self.interval_number)).date()
