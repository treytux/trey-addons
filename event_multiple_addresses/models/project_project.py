###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    address_ids = fields.Many2many(
        string='Extra locations',
        comodel_name='res.partner',
        relation='partner2project_project_rel',
        column1='project_id',
        column2='partner_id',
    )
