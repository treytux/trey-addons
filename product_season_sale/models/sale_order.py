# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season')

    @api.multi
    def action_ship_create(self):
        res = super(SaleOrder, self).action_ship_create()
        for picking in self.picking_ids:
            picking.season_id = self.season_id and self.season_id.id or None
        return res
