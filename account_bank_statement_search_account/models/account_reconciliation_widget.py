###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models
from odoo.osv import expression


class AccountReconcilationWidget(models.AbstractModel):
    _inherit = 'account.reconciliation.widget'

    def _domain_move_lines(self, search_str):
        domain = super()._domain_move_lines(search_str)
        if search_str.startswith('.'):
            return [('account_id.code', '=like', f'{search_str[1:]}%')]
        return expression.OR(
            [domain, [('account_id.code', 'like', search_str)]])
