###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _notify_get_recipients_groups(self, msg_vals=None):
        groups = super()._notify_get_recipients_groups(msg_vals=msg_vals)
        for group in groups:
            if group[0] == 'user':
                continue
            if 'has_button_access' not in group[2]:
                continue
            group[2]['has_button_access'] = False
        return groups
