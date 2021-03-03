###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    main_technical_id = fields.Many2one(
        comodel_name='res.users',
        domain=[('share', '=', False)],
        string='Main technician',
    )
