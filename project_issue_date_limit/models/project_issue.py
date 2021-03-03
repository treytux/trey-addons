# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    date_limit = fields.Datetime(
        string='Date limit',
        default=fields.Datetime.now,
    )
