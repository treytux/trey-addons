# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def line_get_convert(self, line, part, date):
        res = super(AccountInvoice, self).line_get_convert(line, part, date)
        res['subvention_id'] = line.get('subvention_id', None)
        res['subvention_percent'] = line.get('subvention_percent', 0)
        return res

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        if not self.move_id.line_id:
            return res
        subventions = {}
        move2split = None
        invoice = self.move_id.line_id[0].invoice
        for move_line in self.move_id.line_id:
            if move_line.account_id == invoice.account_id:
                move2split = move_line
            if not move_line.subvention_id.exists():
                continue
            percent = move_line.subvention_percent / 100
            balance = (
                (move2split.debit * percent) - (move2split.credit * percent))
            key = (move_line.subvention_id.id, move_line.subvention_percent)
            subventions.setdefault(key, 0)
            subventions[key] += balance
            move_line.subvention_id = None
            move_line.subvention_percent = 0
        if not move2split:
            return res
        move2split.move_id.button_cancel()
        for subvention, balance in subventions.iteritems():
            subvention_id, subvention_percent = subvention
            debit = balance > 0 and balance or 0
            credit = balance < 0 and balance or 0
            move2split.copy({
                'debit': debit,
                'credit': credit,
                'subvention_percent': subvention_percent,
                'subvention_id': subvention_id})
            move2split.debit -= debit
            move2split.credit -= credit
        move2split.move_id.button_validate()
        return res
