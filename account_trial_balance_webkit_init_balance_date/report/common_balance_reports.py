# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2016-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from openerp import tools, osv, _
from openerp.addons.account_financial_report_webkit.report.trial_balance \
    import TrialBalanceWebkit
from openerp.report.interface import report_int
from operator import add


class TrialBalanceDateWebkit(TrialBalanceWebkit):

    def is_initial_balance_enabled(self, main_filter):
        if (self.name == 'account.account_report_trial_balance_webkit' and
                main_filter == 'filter_date'):
            return True
        return super(TrialBalanceDateWebkit, self).is_initial_balance_enabled(
            main_filter)

    def _get_initial_balance_mode(self, start_period):
        if (self.name == 'account.account_report_trial_balance_webkit' and
                isinstance(start_period, unicode)):
            if '-01-01' in start_period:
                return 'opening_balance'
            return 'initial_balance'
        return super(TrialBalanceDateWebkit, self)._get_initial_balance_mode(
            start_period)

    def get_included_opening_period(self, period):
        if (self.name == 'account.account_report_trial_balance_webkit' and
                isinstance(period, unicode)):
            if '01-01' not in period:
                return []
            period_obj = self.pool.get('account.period')
            initial_date = period
            period = period_obj.find(self.cr, self.uid, period)
            if not period:
                raise osv.except_osv(_(
                    'No period found for %s') % initial_date, '')
            period = period_obj.browse(self.cr, self.uid, period[0])
        return super(TrialBalanceDateWebkit, self).get_included_opening_period(
            period)

    def _compute_init_balance_date(self, account_id=None, date_start=None,
                                   mode='computed', default_values=False,
                                   fiscalyear=False):
        res = {}
        if not default_values and fiscalyear:
            if not account_id or not date_start:
                raise Exception('Missing account or period_ids')
            try:
                self.cursor.execute("SELECT sum(debit) AS debit, "
                                    " sum(credit) AS credit, "
                                    " sum(debit)-sum(credit) AS balance, "
                                    " sum(amount_currency) AS curr_balance"
                                    " FROM account_move_line"
                                    " WHERE date >= %s AND date < %s"
                                    " AND account_id = %s",
                                    (fiscalyear.date_start, date_start,
                                     account_id))
                res = self.cursor.dictfetchone()
            except Exception:
                self.cursor.rollback()
                raise
        if not default_values and not fiscalyear:
            if not account_id or not date_start:
                raise Exception('Missing account or period_ids')
            try:
                self.cursor.execute("SELECT sum(debit) AS debit, "
                                    " sum(credit) AS credit, "
                                    " sum(debit)-sum(credit) AS balance, "
                                    " sum(amount_currency) AS curr_balance"
                                    " FROM account_move_line"
                                    " WHERE date < %s"
                                    " AND account_id = %s",
                                    (date_start, account_id))
                res = self.cursor.dictfetchone()
            except Exception:
                self.cursor.rollback()
                raise
        return {'debit': res.get('debit') or 0.0,
                'credit': res.get('credit') or 0.0,
                'init_balance': res.get('balance') or 0.0,
                'init_balance_currency': res.get('curr_balance') or 0.0,
                'state': mode}

    def _compute_initial_balances(self, account_ids, start_period, fiscalyear):
        res = {}
        if (self.name == 'account.account_report_trial_balance_webkit' and
                isinstance(start_period, unicode)):
            for acc in self.pool.get('account.account').browse(self.cursor,
                                                               self.uid,
                                                               account_ids):
                res[acc.id] = self._compute_init_balance(default_values=True)
                res[acc.id] = self._compute_init_balance_date(
                    acc.id, start_period, fiscalyear=fiscalyear)
            return res
        return super(TrialBalanceDateWebkit, self)._compute_initial_balances(
            account_ids, start_period, fiscalyear)

    def _get_account_details(self, account_ids, target_move, fiscalyear,
                             main_filter, start, stop, initial_balance_mode,
                             context=None):
        report = 'account.account_report_trial_balance_webkit'
        if self.name != report or not isinstance(start, unicode):
            return super(TrialBalanceDateWebkit, self)._get_account_details(
                account_ids, target_move, fiscalyear, main_filter, start, stop,
                initial_balance_mode, context)
        ctx = context and context.copy() or {}
        ctx.update({
            'state': target_move,
            'all_fiscalyear': True,
            'date_from': start,
            'date_to': stop})
        account_obj = self.pool.get('account.account')
        init_balance = False
        if initial_balance_mode == 'opening_balance':
            init_balance = self._read_opening_balance(account_ids, start)
        elif initial_balance_mode:
            init_balance = self._compute_initial_balances(
                account_ids, start, fiscalyear)
        if tools.config['test_enable']:
            account_obj._parent_store_compute(self.cursor)
        accounts = account_obj.read(
            self.cursor, self.uid, account_ids,
            ['type', 'code', 'name', 'debit', 'credit', 'balance', 'parent_id',
             'level', 'child_id'], context=ctx)
        re = {}
        for account in accounts:
            re[account['id']] = account
            if not init_balance:
                continue
            child_ids = account_obj._get_children_and_consol(
                self.cursor, self.uid, account['id'], ctx)
            if child_ids:
                child_init_balances = [
                    init_bal['init_balance']
                    for acnt_id, init_bal in init_balance.iteritems()
                    if acnt_id in child_ids]
                top_init_balance = reduce(add, child_init_balances)
                account['init_balance'] = top_init_balance
            else:
                account.update(init_balance[account['id']])
            account['balance'] = (
                account['init_balance'] + account['debit'] - account['credit'])
            if (main_filter == 'filter_date' and
               initial_balance_mode == 'opening_balance'):
                account['balance'] = account['debit'] - account['credit']
            re[account['id']] = account
        return re


rep = report_int._reports['report.account.account_report_trial_balance_webkit']
rep.parser = TrialBalanceDateWebkit
