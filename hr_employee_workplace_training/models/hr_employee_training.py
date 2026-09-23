###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class HrEmployeeTraining(models.Model):
    _name = 'hr.employee.training'
    _description = 'Workplace Courses & Certifications'

    name = fields.Char(
        string='Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    duration = fields.Float(
        string='Duration (hours)',
    )
    date = fields.Date(
        string="Date",
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
    )
