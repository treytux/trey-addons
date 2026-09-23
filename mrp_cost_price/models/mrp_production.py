###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def get_service_values(self, qty_finished):
        self.ensure_one()
        services_value = 0
        bom_line_services = self.bom_id.mapped('bom_line_ids').filtered(
            lambda ln: ln.product_id.type == 'service')
        for bom_line in bom_line_services:
            qty = bom_line.product_qty * qty_finished / self.bom_id.product_qty
            services_value += qty * bom_line.product_id.standard_price
        return services_value

    def get_value(self, consumed_moves, finished_qty):
        self.ensure_one()
        services_value = self.get_service_values(finished_qty)
        phisic_value = sum(
            [c.quantity_done * -c.price_unit for c in consumed_moves])
        return services_value + phisic_value

    def _cal_price(self, consumed_moves):
        res = super()._cal_price(consumed_moves)
        finished_moves = self.move_finished_ids.filtered(
            lambda x: x.state not in ('done', 'cancel')
            and x.quantity_done > 0)
        finished_qty = sum(finished_moves.mapped('quantity_done'))
        raw_value = self.get_value(consumed_moves, finished_qty)
        finished_moves.write({
            'price_unit': raw_value / finished_qty if finished_qty else 0,
            'value': raw_value,
        })
        return res

    def post_inventory(self):
        re = super(MrpProduction, self).post_inventory()
        for move in self.move_finished_ids:
            if move.quantity_done == 0:
                continue
            raw_value = move.remaining_value
            move.write({
                'price_unit': raw_value / move.quantity_done,
                'value': move.remaining_value,
            })
            if move.product_id.cost_method != 'fifo':
                continue
            other_moves = move.search([
                ('id', '!=', move.id),
                ('product_id', '=', move.product_id.id),
            ])
            if other_moves.filtered(lambda m: m.quantity_done != 0):
                continue
            move_sudo = move.product_id.sudo().with_context(
                force_company=move.company_id.id)
            move_sudo.standard_price = move.price_unit
        return re
