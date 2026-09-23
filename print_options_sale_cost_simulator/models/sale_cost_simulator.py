###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class SaleCostSimulator(models.Model):
    _inherit = 'sale.cost.simulator'

    def action_wiz_print_options_sale_cost_simulator(self):
        self.ensure_one()
        wiz_simulator_model = 'wiz.print.options.sale.cost.simulator'
        wiz = self.env[wiz_simulator_model].create({})
        return {
            'name': _('Print'),
            'type': 'ir.actions.act_window',
            'res_model': wiz_simulator_model,
            'view_mode': 'form',
            'res_id': wiz.id,
            'target': 'new',
        }
