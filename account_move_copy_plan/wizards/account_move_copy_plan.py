###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import _, exceptions, fields, models


class AccountMoveCopyPlan(models.TransientModel):
    _name = 'account.move.copy_plan'
    _description = 'Wizard for copy move with a plan'

    period = fields.Selection(
        selection=[
            ('day', 'Days'),
            ('month', 'Months'),
            ('year', 'Year'),
        ],
        string='Period',
        default='month',
        required=True,
    )
    quantity = fields.Integer(
        string='Quantity',
        required=True,
    )

    def _copy_account_move(self, move):
        moves = self.env['account.move']
        for index in range(1, self.quantity + 1):
            if self.period == 'day':
                new_date = move.date + relativedelta(days=index)
            elif self.period == 'month':
                new_date = move.date + relativedelta(months=index)
            elif self.period == 'year':
                new_date = move.date + relativedelta(years=index)
            moves |= move.copy({'date': new_date, 'ref': move.ref})
        return moves

    def create_moves(self):
        assert self._context.get('active_ids'), 'Missing active_ids'
        moves = self.env['account.move'].browse(self._context['active_ids'])
        moves_without_date = moves.filtered(lambda m: not m.date)
        if moves_without_date:
            raise exceptions.UserError(
                _('Moves ID\'s %s don\'t has date') % (moves_without_date.ids))
        created_moves = self.env['account.move']
        for move in moves:
            created_moves |= self._copy_account_move(move)
        return created_moves
