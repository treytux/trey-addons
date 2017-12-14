# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _
import logging
_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_button_confirm(self):
        allow_group_id = self.env.ref(
            'sale_credit_limit.group_view_allow_sell_credit_limit')
        res = [g for g in self.env.user.groups_id.ids
               if g in [allow_group_id.id]]
        info = self.partner_id.get_credit_limit_info(self.amount_total)
        if not res and info['allow']:
            raise exceptions.Warning(_(
                'Partner \'%s\' has exceeded the credit limit.\n'
                'You are not authorized to confirm the order.') %
                self.partner_id.name)
        return super(SaleOrder, self).action_button_confirm()
