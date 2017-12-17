# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class AccountMoveFiscalYearReconcile(models.TransientModel):
    _name = 'account.move.fiscal.year.reconcile'
    _description = 'Wizard for reconcile two account moves'

    move_opening_id = fields.Many2one(
        comodel_name='account.move',
        domain='[("period_id.special", "=", True)]',
        required=True,
        string='Opening move')
    move_closing_id = fields.Many2one(
        comodel_name='account.move',
        domain='[("period_id.special", "=", True)]',
        required=True,
        string='Closing move')
    account_ids = fields.Many2many(
        comodel_name='account.account',
        required=True,
        domain='[("type", "!=", "view")]',
        relation='account_move_reconcile_accounts_rel',
        column1='reconcile_id',
        column2='account_id')

    @api.model
    def default_get(self, fields):
        res = super(AccountMoveFiscalYearReconcile, self).default_get(fields)
        account = self.env['account.account'].search([
            ('type', 'in', ['receivable', 'payable']),
            ('reconcile', '=', True)])
        res['account_ids'] = [(6, 0, account.ids)]
        return res

    @api.multi
    def button_accept(self):
        if self.move_closing_id == self.move_opening_id:
            raise exceptions.Warning(_(
                'You have selected the same account move for reconcile'))

        def _get_move_lines(move, lines=None):
            if lines is None:
                lines = {}
            for line in move.line_id:
                if line.reconcile_id:
                    continue
                if line.account_id.id not in self.account_ids.ids:
                    continue
                key = '%s,%s' % (line.partner_id.id, line.account_id.id)
                lines.setdefault(key, []).append(line)
            return lines

        lines = _get_move_lines(self.move_closing_id)
        lines = _get_move_lines(self.move_opening_id, lines)
        for key, moves in lines.iteritems():
            partner_id, account_id = key.split(',')
            balance = sum([m.debit - m.credit for m in moves])
            if balance != 0:
                raise exceptions.Warning(_(
                    'The balance for partner %s and move lines %s is not 0, '
                    'is %s' % (
                        moves[0].partner_id.name,
                        ','.join([m.name for m in moves]), balance)))
            to_reconcile = self.env['account.move.line'].browse(
                [m.id for m in moves])
            to_reconcile.reconcile()
