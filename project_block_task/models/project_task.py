# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProjectTask(models.Model):
    _inherit = 'project.task'

    project_state = fields.Selection(
        string='Project state',
        related='project_id.state')
