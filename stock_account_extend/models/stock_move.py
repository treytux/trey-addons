# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _get_master_data(self, move, company):
        res = super(StockMove, self)._get_master_data(move, company)
        if self.env.context.get('force_user_id', False):
            res = res[0], self.env.context['force_user_id'], res[2]
        return res
