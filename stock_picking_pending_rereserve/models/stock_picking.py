# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def pending_rereserve_pick(self):
        for picking in self:
            picking.rereserve_quants(
                picking,
                move_ids=[
                    x.id for x in picking.move_lines
                    if x.state not in ('done', 'cancel', 'assigned')])
