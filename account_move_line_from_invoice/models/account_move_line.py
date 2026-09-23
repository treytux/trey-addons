###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        default_move_id = self.env.context.get('default_move_id')
        if default_move_id:
            for vals in vals_list:
                vals.setdefault('move_id', default_move_id)
        return super().create(vals_list)
