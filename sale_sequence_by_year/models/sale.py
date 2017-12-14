# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api
import time


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        date_now = vals.get('date_order', time.strftime('%Y-%m-%d'))
        period_id = self.env['account.period'].find(date_now)
        return super(SaleOrder, self.with_context(
            fiscalyear_id=period_id.fiscalyear_id.id)).create(vals)
