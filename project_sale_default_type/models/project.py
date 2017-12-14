# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class Project(models.Model):
    _inherit = 'project.project'

    sale_order_type_id = fields.Many2one(
        comodel_name='sale.order.type',
        string='Sale Order Type')
