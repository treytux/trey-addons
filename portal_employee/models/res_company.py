###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    holidays_type = fields.Many2many(
        string='Holidays type',
        comodel_name='hr.leave.type',
        relation='res_company2hr_leave_type_holidays_rel',
        column1='hr_leave_type_id',
        column2='company_id',
        help='All holiday types for this company.',
    )
    absences_type = fields.Many2many(
        string='Absences type',
        comodel_name='hr.leave.type',
        relation='res_company2hr_leave_type_absences_rel',
        column1='hr_leave_type_id',
        column2='company_id',
        help='All absence types for this company.',
    )
