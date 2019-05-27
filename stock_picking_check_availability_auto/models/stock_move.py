# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_confirm(self):
        res = super(StockMove, self).action_confirm()
        if not self.env.context.get('auto_picking_assign'):
            return res
        for pick in list(set([m.picking_id for m in self])):
            pick.action_assign()
