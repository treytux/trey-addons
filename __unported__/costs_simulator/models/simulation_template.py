# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

# from osv import osv
# from osv import fields

from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class SimulationTemplate(models.Model):
    _name = 'simulation.template'
    _description = 'Simulation Template'

    name = fields.Char(
        string='Name',
        size=64,
        required="True",
        select=1)
    template_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product for sale')
    purchase_template_lines_ids = fields.One2many(
        comodel_name='simulation.template.line',
        reverse_name='template_id',
        string='Purchase Lines',
        domain=[('type_cost', '=', 'Purchase')])
    investment_template_lines_ids = fields.One2many(
        comodel_name='simulation.template.line',
        reverse_name='template_id',
        string='Investment Lines',
        domain=[('type_cost', '=', 'Investment')])
    subcontracting_template_lines_ids = fields.One2many(
        comodel_name='simulation.template.line',
        reverse_name='template_id',
        string='Subcontracting Lines',
        domain=[('type_cost', '=', 'Subcontracting Services')])
    task_template_lines_ids = fields.One2many(
        comodel_name='simulation.template.line',
        reverse_name='template_id',
        string='Internal Task Lines',
        domain=[('type_cost', '=', 'Task')])
    others_template_lines_ids = fields.One2many(
        comodel_name='simulation.template.line',
        reverse_name='template_id',
        string='Others Lines',
        domain=[('type_cost', '=', 'Others')])

