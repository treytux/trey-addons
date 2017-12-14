# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _


class SaleCostSimulator(models.Model):
    _inherit = 'sale.cost.simulator'

    @api.multi
    def action_wiz_print_options_sale_cost_simulator(self):
        wiz_simulator_model = 'wiz.print.options.sale.cost.simulator'
        wiz = self.env[wiz_simulator_model].create({})
        return {
            'name': _('Print'),
            'type': 'ir.actions.act_window',
            'res_model': wiz_simulator_model,
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wiz.id,
            'target': 'new'}
