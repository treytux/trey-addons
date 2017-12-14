# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_id = fields.Many2one(
        comodel_name='stock.picking.delivery',
        string='Delivery')

    @api.multi
    def open_delivery(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update({'default_picking_id': self.id})
        view_id = self.env.ref('stock_picking_delivery.'
                               'stock_picking_delivery_form_view')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking.delivery',
            'res_id': self.delivery_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id.id,
            'context': ctx,
            'target': 'current'}
