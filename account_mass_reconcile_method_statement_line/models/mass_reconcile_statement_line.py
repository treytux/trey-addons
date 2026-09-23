###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class MassReconcileStatementLine(models.TransientModel):
    _name = 'mass.reconcile.statement.line'
    _inherit = 'mass.reconcile.base'
    _description = 'Mass reconcile statement line'

    def action_reconcile(self, method):
        select = self._select_query()
        select += ', account_move_line.name '
        where, params = self._where_query()
        where += ' AND account_move_line.name IS NOT NULL'
        where += ' AND account_move_line.name ilike %s'
        where += ' AND account_move_line.statement_line_id IS NOT NULL'
        params.append(self._filter)
        order = (
            'ORDER BY date'
            if self.date_base_on == 'oldest' else 'ORDER BY date desc'
        )
        query = ' '.join((select, self._from_query(), where, order))
        self.env.flush_all()
        self.env.cr.execute(query, params)
        res = []
        for line in self.env.cr.dictfetchall():
            move_line = self._create_move_line(line, method)
            if move_line:
                res.append(move_line.id)
        return res

    def _create_move_line(self, line, method):
        move = self.env['account.move'].browse(line['move_id'])
        move_line = move.line_ids.filtered(
            lambda ml: ml.account_id == move.journal_id.suspense_account_id)
        if not move_line:
            return
        if move_line.statement_line_id.is_reconciled:
            return
        if not move_line.debit and not move_line.credit:
            return
        account = (
            method.account_profit_id if move_line.debit
            else method.account_lost_id)
        container = {'records': move, 'self': move}
        with move._check_balanced(container):
            move_line.write({'account_id': account.id})
        return move_line
