# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def recalculate_prices(self):
        for record in self:
            for line in record.order_line:
                if line.agents:
                    for agent in line.agents:
                        agent.unlink()
        return super(SaleOrder, self).recalculate_prices()
