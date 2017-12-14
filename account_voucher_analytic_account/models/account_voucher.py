# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account')

    @api.multi
    def action_move_line_create(self):
        res = super(AccountVoucher, self).action_move_line_create()
        move_lines = self.move_id.line_id
        if self.analytic_account_id.exists():
            for ml in move_lines:
                ml.write({'analytic_account_id': self.analytic_account_id.id})
        valid_move_lines = []
        if self.analytic_account_id.exists():
            for ml in move_lines:
                if ml.credit == 0:
                    valid_move_lines.append(ml.id)
            movelines = self.env['account.move.line'].browse(valid_move_lines)
            movelines.create_analytic_lines()
        return res
