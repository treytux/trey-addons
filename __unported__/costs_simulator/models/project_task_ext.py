# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

# from osv import osv
# from osv import fields

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp

### HEREDO ESTA CLASE PARA AÑADIR DOS CAMPOS NUEVOS AL OBJETO project.task


class Task(models.Model):
    _name = 'project.task'
    _inherit = 'project.task'
     
    # Nombre del producto de coste de la linea de simulación de costes
    cost_product_name = fields.Char(
        string='Cost Product',
        size=64,
        readonly=True)
    # Nombre del producto de venta de la linea de simulación de costes
    sale_product_name = fields.Char(
        string='Sale Product',
        size=64,
        readonly=True),
    # Campo para saber con que proyecto esta relacionado la tarea
    project3_id = fields.Many2one(
        comodel_name='project.project',
        string='Project')
