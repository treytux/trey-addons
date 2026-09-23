###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    lang_ids = fields.One2many(
        comodel_name='hr.employee.lang',
        inverse_name='employee_id',
        string='Spoken Languages',
    )
