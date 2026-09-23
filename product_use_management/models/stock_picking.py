###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    signed_use_management = fields.Boolean(
        string='Is signed',
    )
    products_with_use_management = fields.Boolean(
        string='Products with use management in picking',
        compute='_compute_products_with_use_management',
    )

    @api.depends(
        'move_lines', 'move_line_ids_without_package', 'move_line_ids')
    def _compute_products_with_use_management(self):
        for picking in self:
            picking.products_with_use_management = False
            if picking.get_stock_move_lines_products_use_management():
                picking.products_with_use_management = True

    def get_stock_move_lines_products_use_management(self):
        return self.move_line_ids_without_package.filtered(
            lambda ln: ln.lot_id.product_id.product_tmpl_id.use_management)

    def signed_stock_picking_with_product_use_management(self):
        for line in self.get_stock_move_lines_products_use_management():
            line.lot_id.qc_use_dates.create({
                'date': datetime.now(),
                'user_id': self.env.user.id,
                'picking_id': self.id,
                'product_tmpl_id': line.lot_id.product_id.product_tmpl_id.id,
                'lot_id': line.lot_id.id,
            })
        self.signed_use_management = True

    @api.multi
    def action_done(self):
        res = super().action_done()
        for picking in self:
            if not picking.signed_use_management and any(
                    picking.get_stock_move_lines_products_use_management()):
                raise ValidationError(_('You have to sign the picking.'))
            if picking.state == 'done':
                for line in (
                        self.get_stock_move_lines_products_use_management()):
                    line.lot_id.times_used += 1
        return res
