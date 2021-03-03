###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_open_simulator(self):
        self.ensure_one()
        line_obj = self.env['sale.open.simulator.line']
        lines = []
        for line in self.order_line:
            product = line.product_id
            if not product:
                continue
            cost = (line.standard_price or line.product_id.standard_price)
            lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'standard_price': cost,
                'margin': line_obj._calculate_margin(
                    cost, line.price_unit, line.discount),
                'price_subtotal': line.price_subtotal,
                'sale_line_id': line.id,
            }))
        wizard = self.env['sale.open.simulator'].create({
            'state': (
                self.state in ['sale', 'done', 'cancel']
                and 'readonly' or 'draft'),
            'sale_id': self.id,
            'company_id': self.company_id.id,
            'currency_id': self.pricelist_id.currency_id.id,
            'line_ids': lines,
            'pricelist_id': self.pricelist_id.id,
        })
        action = self.env.ref('sale_simulator.open_simulator_action').read()[0]
        action['res_id'] = wizard.id
        return action
