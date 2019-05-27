# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models
from openerp.tools.float_utils import float_round


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
        precision = self.env['decimal.precision'].precision_get('Account')
        subventions = {}
        invoice = self.move_id.line_id[0].invoice
        move2split = [m for m in self.move_id.line_id
                      if m.account_id == invoice.account_id][0]
        for move_line in self.move_id.line_id:
            if not move_line.subvention_id or not move_line.subvention_percent:
                continue
            percent = move_line.subvention_percent / 100
            balance = float_round(
                (move_line.debit * percent) - (move_line.credit * percent),
                precision)
            key = (move_line.subvention_id.id, move_line.subvention_percent)
            subventions.setdefault(key, 0)
            subventions[key] += balance
            move_line.subvention_id = None
            move_line.subvention_percent = 0
        move2split.move_id.button_cancel()
        for subvention, balance in subventions.iteritems():
            if not balance:
                continue
            subvention_id, subvention_percent = subvention
            move2split.copy({
                'debit': move2split.debit and abs(balance) or 0,
                'credit': move2split.credit and abs(balance) or 0,
                'subvention_percent': subvention_percent,
                'subvention_id': subvention_id})
            move2split.debit -= move2split.debit and abs(balance) or 0
            move2split.credit -= move2split.credit and abs(balance) or 0
        move2split.move_id.button_validate()
        return res
