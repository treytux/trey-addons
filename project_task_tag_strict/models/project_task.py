###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    domain_tag_ids = fields.One2many(
        comodel_name='project.tags',
        compute='_compute_domain_tag_ids',
        string='Allowed tags',
    )

    @api.depends('project_id', 'project_id.tag_ids')
    def _compute_domain_tag_ids(self):
        for task in self:
            if not task.project_id:
                continue
            task.domain_tag_ids = task.project_id.tag_ids.ids
