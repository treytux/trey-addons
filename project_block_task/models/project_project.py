###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    block_timesheet = fields.Boolean(
        string='Block timesheets',
        help='If enabled, timesheets cannot be registered on this project '
             'or on any of its tasks.',
    )
