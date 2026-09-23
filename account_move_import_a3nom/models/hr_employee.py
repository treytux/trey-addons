###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    a3nom_company = fields.Integer(
        string='A3Nom company',
        help='It\'s an integer value',
    )
    a3nom_code = fields.Integer(
        string='A3Nom employee code',
        placeholder='TR00001',
        help='The integer number of the worker\'s code',
    )
