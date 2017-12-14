# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class CustomList(models.Model):
    _name = 'custom.list'
    _description = 'Custom list'

    name = fields.Char(
        string='Name',
        required=True)
    line_ids = fields.One2many(
        string='Lines',
        comodel_name='custom.list.line',
        inverse_name='custom_list_id')


class CustomListLine(models.Model):
    _name = 'custom.list.line'
    _description = 'Custom list line'
    _order = 'sequence, name'

    name = fields.Char(
        string='Empty')
    custom_list_id = fields.Many2one(
        comodel_name='custom.list',
        string='Custom list')
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template')
    sequence = fields.Integer(
        string='Sequence',
        help='Sequence for the handle',
        default=10)
