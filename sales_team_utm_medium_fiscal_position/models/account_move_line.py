###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if hasattr(super(), '_onchange_product_id'):
            res = super()._onchange_product_id()
        else:
            res = {}
        if not self.move_id or not self.move_id.fiscal_position_id:
            return res
        if not hasattr(self.move_id, 'medium_id'):
            return res
        medium_id = self.move_id.medium_id
        if not medium_id:
            return res
        fiscal_position = self.move_id.fiscal_position_id.with_context(
            medium_id=medium_id.id
        )
        mapped_account = fiscal_position.map_account(self.account_id)
        if mapped_account != self.account_id:
            self.account_id = mapped_account
        return res
