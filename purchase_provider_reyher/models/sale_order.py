###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    show_button_simulate_reyher = fields.Boolean(
        string='Show button simulate Reyher',
        compute='_compute_show_button_simulate_reyher',
    )

    @api.depends('order_line.product_id')
    def _compute_show_button_simulate_reyher(self):
        connector = self.env['connector.supplier'].search([
            ('supplier_mode', '=', 'reyher'),
        ], limit=1)
        for sale in self:
            sale.show_button_simulate_reyher = any(
                line.product_id.seller_ids.filtered(
                    lambda s: s.name == connector.supplier_id)
                for line in sale.order_line)

    def action_simulator_sale_reyher(self):
        module_name = 'purchase_provider_base'
        action_name = 'connector_simulator_sale_action'
        action = self.env.ref('%s.%s' % (module_name, action_name)).read()[0]
        wizard = self.env['connector.simulator.sale'].create({
            'supplier_mode': 'reyher',
            'order_id': self.id,
            'simulate_order_date_reyher': fields.Date.today(),
        })
        lines = self.env['connector.simulator.sale.line']
        connector = self.env['connector.supplier'].search([
            ('supplier_mode', '=', 'reyher'),
        ], limit=1)
        for line in self.order_line:
            supplierinfos = line.product_id.seller_ids.filtered(
                lambda sp: sp.name == connector.supplier_id)
            if not supplierinfos:
                continue
            lines.create({
                'sale_id': wizard.id,
                'sale_line_id': line.id,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'cost_price': line.product_id.standard_price,
            })
        action['res_id'] = wizard.id
        return action
