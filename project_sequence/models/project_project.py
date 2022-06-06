###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    code = fields.Char(
        string='Code',
    )

    @api.model
    def create(self, vals):
        if 'code' not in vals:
            vals['code'] = self.env['ir.sequence'].next_by_code(
                'project.sequence')
        return super().create(vals)
