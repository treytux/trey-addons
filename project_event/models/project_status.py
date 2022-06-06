###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectStatus(models.Model):
    _inherit = 'project.status'

    not_modify_event = fields.Boolean(
        string='Not allow modify event',
    )
