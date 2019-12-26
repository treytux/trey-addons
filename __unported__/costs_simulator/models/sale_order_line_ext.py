# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

# from osv import osv
# from osv import fields

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'
     
    # Este campo estaba de CTA pero ahora no se usara
    simulation_cost_line_ids = fields.One2many(
        comodel_name='simulation.cost.line',
        inverse_name='sale_order_line_id',
        string='Simulation Costs Lines')
    # Campo para saber si tengo que generar abastecimeintos
    clear_procurement = fields.Boolean(
        string='Crear Procurement')
