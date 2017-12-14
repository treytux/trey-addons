# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _, exceptions


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.one
    def action_paid(self):
        if self.session_id.config_id.same_sign:
            amounts = [
                l.price_subtotal for l in self.lines if l.price_subtotal != 0]
            count = abs(sum([a > 0 and 1 or -1 for a in amounts]))
            if count != len(amounts):
                raise exceptions.Warning(_(
                    'All lines must be with the same sign, positive or '
                    'negative'))
        return super(PosOrder, self).action_paid()
