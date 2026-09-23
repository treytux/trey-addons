###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from collections import defaultdict

from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    @api.depends('line_ids.amount')
    def _compute_debit_credit_balance(self):
        res = super()._compute_debit_credit_balance()
        Curr = self.env['res.currency']
        analytic_line_obj = self.env['account.analytic.line']
        domain = [
            ('account_id', 'in', self.ids),
            ('company_id', 'in', [False] + self.env.companies.ids),
            '|',
            ('sheet_state', '=', 'done'),
            '&',
            ('sheet_id', '=', False),
            '|',
            ('task_id', '=', False),
            ('employee_id', '=', False)
        ]
        if self._context.get('from_date', False):
            domain.append(('date', '>=', self._context['from_date']))
        if self._context.get('to_date', False):
            domain.append(('date', '<=', self._context['to_date']))
        user_currency = self.env.company.currency_id
        credit_groups = analytic_line_obj.read_group(
            domain=domain + [('amount', '>=', 0.0)],
            fields=['account_id', 'currency_id', 'amount'],
            groupby=['account_id', 'currency_id'],
            lazy=False,
        )
        data_credit = defaultdict(float)
        for group in credit_groups:
            data_credit[group['account_id'][0]] += \
                Curr.browse(group['currency_id'][0])._convert(
                    group['amount'], user_currency, self.env.company,
                    fields.Date.today())
        debit_groups = analytic_line_obj.read_group(
            domain=domain + [('amount', '<', 0.0)],
            fields=['account_id', 'currency_id', 'amount'],
            groupby=['account_id', 'currency_id'],
            lazy=False,
        )
        data_debit = defaultdict(float)
        for group in debit_groups:
            data_debit[group['account_id'][0]] += \
                Curr.browse(group['currency_id'][0])._convert(
                    group['amount'], user_currency, self.env.company,
                    fields.Date.today())
        for account in self:
            account.debit = abs(data_debit.get(account.id, 0.0))
            account.credit = data_credit.get(account.id, 0.0)
            account.balance = account.credit - account.debit
        return res
