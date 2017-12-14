# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    project_state = fields.Selection(
        string='Project state',
        related='project_id.state')
