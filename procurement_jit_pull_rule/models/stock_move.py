# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _create_procurement(self, move):
        res = super(StockMove, self)._create_procurement(move)
        if move.rule_id and move.rule_id.active_jit:
            procurement = self.env['procurement.order'].browse(res)
            procurement.run()
            procurement.check()
        return res
