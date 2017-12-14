# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, exceptions, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    def action_transfer_picking(self):
        picking = self.picking_ids[0]
        if picking.state == 'draft':
            picking.action_confirm()
        if picking.state == 'confirmed':
            picking.action_assign()
        if picking.state == 'partially_available':
            raise exceptions.Warning(_(
                'No stock for transfer picking, automatic operation cancelled.'
                '\nPlease transfer picking manually'))
        if picking.state == 'assigned':
            picking.do_transfer()
