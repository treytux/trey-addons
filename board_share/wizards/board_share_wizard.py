###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class BoardShareWizard(models.TransientModel):
    _name = 'board.share.wizard'
    _description = 'Share Dashboard'

    name = fields.Char(
        string='Name',
        required=True,
    )
    user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='board_share_wizard_res_users_rel',
        column1='wizard_id',
        column2='user_id',
        string='Users',
        required=True,
    )

    def action_share(self):
        self.ensure_one()
        self.env['board.share.dashboard'].create({
            'name': self.name,
            'recipient_ids': [(6, 0, self.user_ids.ids)],
        })
        return {'type': 'ir.actions.act_window_close'}
