# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api
import logging

_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    carrier_tracking_ref = fields.Char(
        string='Carrier Tracking Ref',
        copy=False)

    @api.multi
    def action_ship_create(self):
        res = super(SaleOrder, self).action_ship_create()
        if self.picking_ids:
            self.picking_ids[0].carrier_tracking_ref = (
                self.carrier_tracking_ref)
        return res
