# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_explode(self, cr, uid, move, context=None):
        if context is None:
            context = {}
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        context = context.copy()
        property_ids = context.setdefault('property_ids', [])
        property_ids.append('company:%s' % user.company_id.id)
        return super(StockMove, self)._action_explode(
            cr, uid, move, context=context)
