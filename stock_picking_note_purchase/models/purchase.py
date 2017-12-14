# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def action_picking_create(self):
        picking_id = super(PurchaseOrder, self).action_picking_create()
        picking = self.env['stock.picking'].browse(picking_id)
        picking.write(
            {'note': self.notes and self.notes or ''})
        return picking_id
