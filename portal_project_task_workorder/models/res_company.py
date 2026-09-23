###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    workorders_project = fields.Many2one(
        comodel_name='project.project',
        string='Workorders project',
    )
