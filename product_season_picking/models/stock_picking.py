# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season')

    @api.model
    def _create_invoice_from_picking(self, picking, vals):
        vals['season_id'] = (
            picking and picking.season_id and picking.season_id.id or
            vals.get('season_id'))
        return super(StockPicking, self)._create_invoice_from_picking(
            picking, vals)
