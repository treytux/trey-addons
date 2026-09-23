###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectType(models.Model):
    _inherit = 'project.type'

    hr_holidays_public_id = fields.Many2one(
        comodel_name='hr.holidays.public',
        string='Public Holidays',
    )
