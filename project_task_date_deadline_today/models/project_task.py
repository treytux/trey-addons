# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    date_deadline = fields.Date(
        default=lambda s: fields.Date.today(),
    )
