###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class AccountMoveTemplateRun(models.TransientModel):
    _inherit = 'account.move.template.run'

    times = fields.Integer(
        default=1,
        string='Entries Number',
    )
    period = fields.Selection(
        selection=[
            ('days', 'Daily'),
            ('weeks', 'Weekly'),
            ('months', 'Monthly'),
            ('quarter', 'Quarter'),
            ('years', 'Yearly'),
        ],
        default='months',
    )
    only_end_month = fields.Boolean()

    @api.onchange('only_end_month')
    def _onchange_only_end_month(self):
        if self.only_end_month:
            self.date += relativedelta(day=31)

    @api.multi
    def generate_move(self):
        self.ensure_one()
        sequence2amount = {}
        if self.times == 1:
            return super().generate_move()
        for wizard_line in self.line_ids:
            sequence2amount[wizard_line.sequence] = wizard_line.amount
        precision = self.company_id.currency_id.rounding
        self.template_id.compute_lines(sequence2amount)
        if all([float_is_zero(x, precision_rounding=precision)
                for x in sequence2amount.values()]):
            raise UserError(_('Debit and credit of all lines are null.'))
        moves = self.env['account.move']
        for time in range(self.times):
            move_values = self._prepare_move()
            if self.period == 'quarter':
                move_values['date'] = self.date + relativedelta(
                    months=time * 3)
            else:
                move_values['date'] = self.date + relativedelta(
                    **{self.period: time})
            if self.only_end_month:
                move_values['date'] += relativedelta(day=31)
            for line in self.template_id.line_ids:
                amount = sequence2amount[line.sequence]
                if not float_is_zero(amount, precision_rounding=precision):
                    move_values['line_ids'].append(
                        (0, 0, self._prepare_move_line(line, amount)))
            move = self.env['account.move'].create(move_values)
            move.line_ids.write({'date_maturity': move.date})
            moves |= move
        action = self.env.ref('account.action_move_journal_line')
        result = action.read()[0]
        tree_view = self.env.ref('account.view_move_tree')
        form_view = self.env.ref('account.view_move_form')
        result.update({
            'name': _('Entry from template %s') % self.template_id.name,
            'domain': [('id', 'in', moves.ids)],
            'views': [
                (tree_view.id, 'tree'),
                (form_view.id, 'form'),
            ],
            'view_mode': 'form,tree,kanban',
            'context': self.env.context,
        })
        return result
