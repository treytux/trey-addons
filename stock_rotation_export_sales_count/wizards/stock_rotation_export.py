###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class StockRotationExport(models.TransientModel):
    _inherit = 'stock.rotation.export'

    def get_data_row(self, sql_columns_dict):
        res = super().get_data_row(sql_columns_dict)
        product = sql_columns_dict['product']
        location = sql_columns_dict['location']
        moves = self.env['stock.move'].search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id),
            ('state', '=', 'done'),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ])
        res.update({
            _('Sales count'): len(moves.mapped('picking_id.sale_id')),
        })
        return res
