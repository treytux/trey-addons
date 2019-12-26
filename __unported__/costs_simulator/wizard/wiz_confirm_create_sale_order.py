# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

# from osv import osv
# from osv import fields
# from tools.translate import _
# import netsvc
 
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class WizConfirmCreateSaleOrder(models.TransientModel):
    _name = "wiz.confirm.create.sale.order"
    
    def generate_by_line(self):
        # simulation_cost_obj = self.env['simulation.cost']
        simulation_cost_id = self.env.context['active_id']
        self.env['simulation.cost'].write(
            simulation_cost_id, {'generate_by_line': True})
        self.env['simulation.cost'].button_create_sale_order(simulation_cost_id)
        return {'type': 'ir.actions.act_window_close'}

    def generate_by_product_of_template(self):
        # simulation_cost_obj = self.env['simulation.cost']
        simulation_cost_id = self.env.context['active_id']
        self.env['simulation.cost'].write(
            simulation_cost_id, {'generate_by_line': False})
        self.env['simulation.cost'].button_create_sale_order(simulation_cost_id)
        return {'type': 'ir.actions.act_window_close'}
