# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def create_returns(self):
        res = super(StockReturnPicking, self).create_returns()
        picking = self.env['stock.picking'].browse(
            self.env.context.get('active_id'))
        if picking and picking.claim_id:
            res['name'] = _('Return Shipment'),
        return res
