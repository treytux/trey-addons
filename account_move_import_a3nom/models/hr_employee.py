###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    a3nom_company = fields.Integer(
        string='A3Nom company',
        help='It\'s an integer value',
        groups='hr.group_hr_user',
    )
    a3nom_code = fields.Integer(
        string='A3Nom employee code',
        help='The integer number of the worker\'s code',
        groups='hr.group_hr_user',
    )
