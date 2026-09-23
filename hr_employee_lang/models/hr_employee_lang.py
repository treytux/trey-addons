###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class HrEmployeeLang(models.Model):
    _name = 'hr.employee.lang'
    _description = 'Employee Spoken Languages'

    name = fields.Char(
        string='Name',
        required=True,
    )
    level = fields.Char(
        string='Level',
    )
    certificate = fields.Char(
        string='Certificate',
    )
    certification_date = fields.Date(
        string="Certification Date",
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
    )
