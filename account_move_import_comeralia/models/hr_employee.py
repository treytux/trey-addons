###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    comeralia_name = fields.Char(
        string='Name in Comeralia',
    )
    comeralia_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account 640 when import',
    )
    comeralia_account_advance_id = fields.Many2one(
        comodel_name='account.account',
        string='Account for advance',
        help='Account for advance (in spain 460) when import',
    )
    comeralia_project_task_id = fields.Many2one(
        comodel_name='project.task',
        string='Project task when import',
    )
