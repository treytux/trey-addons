# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProjectTaskWork(models.Model):
    _inherit = 'project.task.work'

    real_time = fields.Float(
        string='Real time')
