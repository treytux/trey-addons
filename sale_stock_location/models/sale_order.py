# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Force Source Location')

    @api.one
    def action_button_confirm(self):
        res = super(SaleOrder, self).action_button_confirm()
        if self.location_id:
            for picking in self.picking_ids:
                for line in picking.move_lines:
                    line.location_id = self.location_id.id
        return res
