# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    project_state = fields.Selection(
        string='Project state',
        related='project_id.state')
    task_state = fields.Selection(
        string='Task state',
        related='task_id.kanban_state')
