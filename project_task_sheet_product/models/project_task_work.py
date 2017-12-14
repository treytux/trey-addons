# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class ProjectTaskWork(models.Model):
    _inherit = 'project.task.work'

    product_id = fields.Many2one(
        comodel_name='product.product',
        related='hr_analytic_timesheet_id.product_id',
        domain=[('type', '=', 'service')],
        string='Product')
