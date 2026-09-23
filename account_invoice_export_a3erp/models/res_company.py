###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    company_code_a3erp = fields.Char(
        string='Company code a3ERP',
        size=4,
    )
    office_code_a3erp = fields.Char(
        string='Office code a3ERP',
        size=4,
    )
