# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_ship_create(self):
        res = super(SaleOrder, self).action_ship_create()
        for picking in self.picking_ids:
            picking.note = self.note
        return res
