###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    stock_move_ids = fields.Many2many(
        comodel_name='stock.move',
        string='Stock moves',
        compute='_compute_stock_move_ids',
    )
    stock_move_return_ids = fields.Many2many(
        comodel_name='stock.move',
        string='Stock moves return',
        compute='_compute_stock_move_ids',
    )
    qty_sold = fields.Float(
        string='Quantity sold',
        compute='_compute_qty_sold',
        help='Quantity sold at the stock warehouse orderpoint location.',
    )

    @api.depends('location_id', 'stock_move_ids.state')
    def _compute_stock_move_ids(self):
        move_obj = self.env['stock.move']
        for orderpoint in self:
            orderpoint.stock_move_ids = move_obj.search([
                ('product_id', '=', orderpoint.product_id.id),
                ('location_id', '=', orderpoint.location_id.id),
                ('sale_line_id', '!=', None),
                ('state', '!=', 'cancel'),
            ])
            orderpoint.stock_move_return_ids = move_obj.search([
                ('product_id', '=', orderpoint.product_id.id),
                ('location_dest_id', '=', orderpoint.location_id.id),
                ('sale_line_id', '!=', None),
                ('state', '!=', 'cancel'),
            ])

    @api.depends('location_id', 'stock_move_ids.state')
    def _compute_qty_sold(self):
        for orderpoint in self:
            orderpoint.qty_sold = (
                sum(orderpoint.stock_move_ids.mapped('product_uom_qty'))
                - sum(orderpoint.stock_move_return_ids.mapped(
                    'product_uom_qty')))
