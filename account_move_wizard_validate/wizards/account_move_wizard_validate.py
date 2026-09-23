###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountMoveWizardValidate(models.TransientModel):
    _name = 'account.move.wizard.validate'
    _description = 'Wizard to validate account move'

    date = fields.Date(
        string='Date',
        default=fields.Date.today(),
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name='account.move.wizard.validate.line',
        inverse_name='wizard_id',
        string='Validated account moves',
    )
    step = fields.Integer(
        string='Step',
        default=0,
    )

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {'wizard_id': self.id},
        }

    def button_accept(self):
        assets = self.env['account.asset'].search([
            ('state', '=', 'open'),
        ])
        for asset in assets:
            moves = asset.account_move_line_ids.mapped('move_id').filtered(
                lambda m: m.date <= self.date and m.state == 'draft')
            for move in moves:
                move.post()
                self.env['account.move.wizard.validate.line'].create({
                    'wizard_id': self.id,
                    'asset_id': asset.id,
                    'account_move_id': move.id,
                    'state': move.state,
                })
        self.step = 1
        return self._reopen_view()


class AccountMoveWizardValidateLine(models.TransientModel):
    _name = 'account.move.wizard.validate.line'
    _description = 'Wizard lines'

    wizard_id = fields.Many2one(
        comodel_name='account.move.wizard.validate',
        string='Wizard',
    )
    asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset',
    )
    account_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Account move',
    )
