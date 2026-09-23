###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProjectGroupStatus(models.Model):
    _name = 'project.group.status'
    _description = 'Project groups status'
    _order = 'status_sequence'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
    )
    description = fields.Char(
        string='Description',
        translate=True,
    )
    status_sequence = fields.Integer(
        string='Sequence',
    )
    is_closed = fields.Boolean(
        string='Is Closed Status',
        help='Specify if this is a closing status.',
    )
    fold = fields.Boolean(
        string='Folded',
    )

    @api.model
    def create(self, vals):
        vals['status_sequence'] = self.env['ir.sequence'].next_by_code(
            'project.group.status')
        return super().create(vals)
