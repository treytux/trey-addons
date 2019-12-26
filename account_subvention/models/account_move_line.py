###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    subvention_percent = fields.Float(
        string='Subvention (%)',
        readonly=True,
    )
    subvention_id = fields.Many2one(
        comodel_name='account.subvention',
        string='Subvention',
        readonly=True,
    )

    @api.multi
    def action_subvention_reconcile(self):
        self.ensure_one()
        if self.reconciled:
            raise exceptions.Warning(_(
                'Account move line is reconciled.'))
        if not self.subvention_id:
            raise exceptions.Warning(_(
                'Account move line has not associated subvention.'))
        move = self.env['account.move'].create({
            'name': self.subvention_id.name,
            'partner_id': self.partner_id.id,
            'journal_id': self.subvention_id.journal_id.id,
            'date': self.invoice.date_invoice,
        })
        self.create({
            'move_id': move.id,
            'partner_id': move.partner_id.id,
            'journal_id': move.journal_id.id,
            'date': move.date,
            'name': self.subvention_id.name,
            'account_id': self.subvention_id.account_id.id,
            'debit': self.debit,
            'credit': self.credit})
        move_line = self.create({
            'move_id': move.id,
            'partner_id': move.partner_id.id,
            'journal_id': move.journal_id.id,
            'date': move.date,
            'name': self.subvention_id.name,
            'account_id': self.account_id.id,
            'debit': self.credit,
            'credit': self.debit})
        self.env['account.move.reconcile'].create({
            'line_id': [(6, 0, [self.id, move_line.id])],
            'type': 'auto'})
        move.button_validate()
        return True

    @api.multi
    def cron_reconcile_account_move_lines_subvention(self):
        move_lines2reconcile = self.search([
            ('subvention_id', '!=', False), ('reconciled', '=', False)])
        for move_line in move_lines2reconcile:
            move_line.action_subvention_reconcile()
