###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models


class SaleCostSimulator(models.Model):
    _inherit = 'sale.cost.simulator'

    @api.multi
    def action_print_options_sale_cost_simulator(self):
        wiz_simulator_model = 'print.options.sale.cost.simulator'
        wiz = self.env[wiz_simulator_model].create({})
        return {
            'name': _('Print'),
            'type': 'ir.actions.act_window',
            'res_model': wiz_simulator_model,
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wiz.id,
            'target': 'new',
        }
