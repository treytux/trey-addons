# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, _


class CostSimulator(models.Model):
    _inherit = 'simulation.cost'

    @api.multi
    def action_print_options_cost_simulator(self):
        wiz = self.env['wiz.print.options.cost.simulator'].create({})
        return {
            'name': _('Print'),
            'type': 'ir.actions.act_window',
            'res_model': 'wiz.print.options.cost.simulator',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wiz.id,
            'target': 'new'}
