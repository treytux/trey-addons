# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

# from osv import osv
# from osv import fields

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp

### HEREDO ESTA CLASE PARA AÑADIR CAMPOS AL PROJECTO


class Project(models.Model):
    _name = 'project.project'
    _inherit = 'project.project'
     
    purchase_order_ids = fields.One2many(
        comodel_name = 'purchase.order',
        inverse_name= 'project2_id',
        string="Project Purchase Orders")
    # Campo para saber con que pedido de venta esta relacionado el proyecto
    sale_order_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name='project2_id',
        help="Project tasks")
    # Campo para saber con que siulcion esta relacionado el projecto
    simulation_cost_id = fields.Many2one(
        comodel_name='simulation.cost',
        string='Simulation Cost')
    # Campo para saber con que siulcion esta relacionado el subproyecto
    simulation_cost_id2 = fields.Many2one(
        comodel_name='simulation.cost',
        string='Simulation Cost')
    ### Campo para saber si es un proyecto
    is_project = fields.Boolean(
        string='Is Project')
    # Campo para saber los pedidos de compra relacionados con el proyecto
    purchase_order_ids2 = fields.One2many(
        comodel_name='purchase.order',
        inverse_name='project3_id',
        string="Project Purchase Orders")
    # Campo para saber con que tareas esta relacionados con el proyecto
    task_ids2 = fields.One2many(
        comodel_name='project.task',
        inverse_name='project3_id',
        help="Project Task")
    ### Campo para saber si es un subprojecto
    is_subproject = fields.Boolean(
        string='Is Subproject')

    def ButtonAnalyticalStructureUpdateCosts(self):

       return True
    # def onchange_purchase_ids(self, cr, uid, ids, purchase_list, context={}):
    #     res={}
    #     return {'value':res}
    #
