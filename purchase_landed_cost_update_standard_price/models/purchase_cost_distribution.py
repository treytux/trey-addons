##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError


class PurchaseCostDistribution(models.Model):
    _inherit = 'purchase.cost.distribution'

    reference = fields.Char()

    def action_done(self):
        self.ensure_one()
        Layer = self.env['stock.valuation.layer']
        lines = {}
        for line in self.cost_lines:
            product = line.move_id.product_id
            if (line.move_id.location_id.usage != 'supplier'):
                continue
            lines.setdefault(product, [])
            lines[product].append((
                line.move_id,
                line.standard_price_new - line.standard_price_old))
        for product, vals_list in lines.items():
            if product.cost_method == 'average':
                self._product_price_update(product, vals_list)
            for move, price_diff in vals_list:
                layers = Layer.search([
                    ('product_id', '=', product.id),
                    ('stock_move_id', '=', move.id),
                ])
                for layer in layers:
                    if product.cost_method == 'fifo':
                        candidates = product._get_fifo_candidates(
                            self.env.company)
                        if layer == candidates[0]:
                            self._product_price_update(
                                product,
                                [(candidates[0].stock_move_id, price_diff)])
                            layer.remaining_value = (
                                (layer.unit_cost + price_diff)
                                * layer.remaining_qty)
                    layer.sudo().write({
                        'unit_cost': layer.unit_cost + price_diff,
                        'value': layer.value + price_diff * layer.quantity,
                        'description': f'{layer.description} {self.name}',
                        'reference': self.name,
                    })
        return super().action_done()

    def action_draft(self):
        self.ensure_one()
        Layer = self.env['stock.valuation.layer']
        lines = {}
        for line in self.cost_lines:
            product = line.move_id.product_id
            if (line.move_id.location_id.usage != 'supplier'):
                continue
            if self.currency_id.compare_amounts(
                    line.move_id.price_unit,
                    line.standard_price_new) != 0:
                raise UserError(_(
                    'Cost update cannot be undone because there has been a '
                    'later update. Restore correct price and try again.'))
            lines.setdefault(product, [])
            layer = Layer.search([
                ('product_id', '=', product.id),
                ('stock_move_id', '=', line.move_id.id),
            ], limit=1)
            lines[product].append(
                (line.move_id,
                 line.standard_price_new - layer.unit_cost))
        for product, vals_list in lines.items():
            if product.cost_method == 'average':
                self._product_price_update(product, vals_list)
            for move, price_diff in vals_list:
                layers = Layer.search([
                    ('product_id', '=', product.id),
                    ('stock_move_id', '=', move.id),
                ])
                for layer in layers:
                    if product.cost_method == 'fifo':
                        candidates = product._get_fifo_candidates(
                            self.env.company)
                        if layer == candidates[0]:
                            self._product_price_update(
                                product,
                                [(candidates[0].stock_move_id, price_diff)])
                            layer.remaining_value = (
                                (layer.unit_cost + price_diff)
                                * layer.remaining_qty)
                    layer.sudo().write({
                        'unit_cost': layer.unit_cost + price_diff,
                        'value': layer.value + price_diff * layer.quantity,
                        'description': f'{layer.description} {self.name}',
                        'reference': self.name,
                    })
        return super().action_draft()
