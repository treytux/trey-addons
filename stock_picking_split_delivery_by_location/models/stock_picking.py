###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_availability_text(self, product):
        lines = []
        for warehouse in self.env['stock.warehouse'].search([]):
            qty = product.with_context(warehouse=warehouse.id).qty_available
            lines.append('%s: %i' % (warehouse.name, qty))
        return ', '.join(lines)

    def action_open_delivery_distribution(self):
        module_name = 'stock_picking_split_delivery_by_location'
        action_name = 'stock_picking_distribution_action'
        action = self.env.ref('%s.%s' % (module_name, action_name)).read()[0]
        wizard = self.env['stock.distribution'].create({
            'picking_id': self.id,
        })
        lines = self.env['stock.distribution.line']
        for line in self.move_ids:
            available_text = self._get_availability_text(line.product_id)
            line_data = {
                'wizard_id': wizard.id,
                'product_id': line.product_id.id,
                'qty_requested': line.product_uom_qty,
                'availability_text': available_text,
            }
            lines |= lines.create(line_data)
        action['res_id'] = wizard.id
        return action
