# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class HrAnalyticTimesheet(models.Model):
    _inherit = 'hr.analytic.timesheet'

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='MRP Production')
