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
        if self.env.context.get('group_by_user', False):
            res = res[0], self.env.uid, res[2]
        return res
