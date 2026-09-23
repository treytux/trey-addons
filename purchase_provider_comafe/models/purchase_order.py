###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    show_button_simulate_comafe = fields.Boolean(
        string='Show button simulate Comafe',
        compute='_compute_show_button_simulate_comafe',
    )

    @api.depends('order_line.product_id')
    def _compute_show_button_simulate_comafe(self):
        connector = self.env['connector.supplier'].search([
            ('supplier_mode', '=', 'comafe'),
        ], limit=1)
        for purchase in self:
            purchase.show_button_simulate_comafe = any(
                line.product_id.seller_ids.filtered(
                    lambda s: s.name == connector.supplier_id)
                for line in purchase.order_line)

    def action_simulator_purchase_comafe(self):
        module_name = 'purchase_provider_base'
        action_name = 'connector_simulator_purchase_action'
        action = self.env.ref('%s.%s' % (module_name, action_name)).read()[0]
        wizard = self.env['connector.simulator.purchase'].create({
            'supplier_mode': 'comafe',
            'order_id': self.id,
            'simulate_order_date_comafe': fields.Date.today(),
        })
        lines = self.env['connector.simulator.purchase.line']
        connector = self.env['connector.supplier'].search([
            ('supplier_mode', '=', 'comafe'),
        ], limit=1)
        for line in self.order_line:
            supplierinfos = line.product_id.seller_ids.filtered(
                lambda sp: sp.name == connector.supplier_id)
            if not supplierinfos:
                continue
            lines.create({
                'purchase_id': wizard.id,
                'purchase_line_id': line.id,
                'cost_price': line.product_id.standard_price,
            })
        action['res_id'] = wizard.id
        return action
