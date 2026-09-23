###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class PurchaseCostDistribution(models.Model):
    _inherit = 'purchase.cost.distribution'

    @api.multi
    def action_done(self):
        self.ensure_one()
        if self.cost_update_type != 'direct':
            return
        lines = self.cost_lines.filtered(
            lambda line:
                line.move_id.product_id.cost_method in ('fifo', 'standard')
                and line.move_id.location_id.usage == 'supplier')
        for line in lines:
            price_unit_diff = line.standard_price_new - line.standard_price_old
            line.move_id.move_line_ids._apply_price_unit_diff(price_unit_diff)
            if line.move_id.product_id.cost_method != 'fifo':
                continue
            if line.move_id.remaining_qty == 0:
                continue
            moves = line.move_id.product_id.stock_move_ids.filtered(
                lambda m: m.remaining_qty > 0 and m.state == 'done')
            moves = moves.sorted('date')
            if not moves or moves[0] != line.move_id:
                continue
            line.move_id.product_id.standard_price = line.move_id.price_unit
        return super().action_done()

    @api.multi
    def action_cancel(self):
        self.ensure_one()
        if self.cost_update_type != 'direct':
            return
        lines = self.cost_lines.filtered(
            lambda line:
                line.move_id.product_id.cost_method in ('fifo', 'standard')
                and line.move_id.location_id.usage == 'supplier')
        for line in lines:
            price_unit_diff = line.standard_price_old - line.standard_price_new
            line.move_id.move_line_ids._apply_price_unit_diff(
                price_unit_diff)
            if line.move_id.product_id.cost_method != 'fifo':
                continue
            if line.move_id.remaining_qty == 0:
                continue
            moves = line.move_id.product_id.stock_move_ids.filtered(
                lambda m: m.remaining_qty > 0 and m.state == 'done')
            moves = moves.sorted('date')
            if not moves or moves[0] != line.move_id:
                continue
            line.move_id.product_id.standard_price = line.move_id.price_unit
        return super().action_cancel()
