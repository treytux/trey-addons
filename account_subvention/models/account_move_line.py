# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields, exceptions, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    subvention_percent = fields.Float(
        string='Subvention (%)',
        readonly=True)
    subvention_id = fields.Many2one(
        comodel_name='account.subvention',
        string='Subvention',
        readonly=True)

    @api.one
    def action_subvention_reconcile(self):
        if self.reconcile_id:
            raise exceptions.Warning(_(
                'Acccount move line is reconciled.'))
        if not self.subvention_id:
            raise exceptions.Warning(_(
                'Acccount move line has not associated subvention.'))
        move = self.env['account.move'].create({
            'name': self.subvention_id.name,
            'partner_id': self.partner_id and self.partner_id.id or None,
            'journal_id': self.subvention_id.journal_id.id})
        self.create({
            'move_id': move.id,
            'partner_id': move.partner_id.id or None,
            'journal_id': move.journal_id.id or None,
            'period_id': move.period_id.id,
            'name': self.subvention_id.name,
            'account_id': self.subvention_id.account_id.id,
            'debit': self.debit,
            'credit': self.credit})
        move_line = self.create({
            'move_id': move.id,
            'partner_id': move.partner_id.id or None,
            'journal_id': move.journal_id.id or None,
            'period_id': move.period_id.id,
            'name': self.subvention_id.name,
            'account_id': self.account_id.id,
            'debit': self.credit,
            'credit': self.debit})
        self.env['account.move.reconcile'].create({
            'line_id': [(6, 0, [self.id, move_line.id])],
            'type': 'auto'})
        return True

    @api.multi
    def cron_reconcile_account_move_lines_subvention(self):
        move_lines2reconcile = self.search([
            ('subvention_id', '!=', False), ('reconcile_id', '=', False)])
        for move_line in move_lines2reconcile:
            move_line.action_subvention_reconcile()
