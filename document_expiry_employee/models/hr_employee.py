###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    expiry_docs_ids = fields.One2many(
        comodel_name='document.expiry',
        inverse_name='employee_id',
        string='Documentation',
    )
