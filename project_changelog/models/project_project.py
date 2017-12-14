# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProjectProject(models.Model):
    _inherit = 'project.project'

    changelog_ids = fields.One2many(
        comodel_name='project.changelog',
        inverse_name='project_id',
        string='Changes',
        copy=True)
