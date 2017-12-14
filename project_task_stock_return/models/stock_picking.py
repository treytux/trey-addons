# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task')
    project_id = fields.Many2one(
        comodel_name='account.analytic.account',
        domain="[('partner_id', '=', partner_id)]",
        string='Project')
