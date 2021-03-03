# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import _, exceptions, models, api


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    @api.multi
    def check(self):
        pos_order_ids = self.env.context['active_ids']
        for pos_order in self.env['pos.order'].browse(pos_order_ids):
            partner = pos_order.partner_id
            if partner and partner.is_blocking(pos_order.amount_total):
                raise exceptions.Warning(_(
                    'Partner \'%s\' has exceeded the credit limit.\n'
                    'You are not authorized to confirm the order.') %
                    pos_order.partner_id.name)
        return super(PosMakePayment, self).check()
