# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _get_master_data(self, move, company):
        res = super(StockMove, self)._get_master_data(move, company)
        res = list(res)
        res[1] = False
        return tuple(res)
