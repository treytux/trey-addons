###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product in invoice',
        domain=[
            ('type', '=', 'service'),
            ('invoice_policy', '=', 'delivery'),
            ('service_type', '=', 'timesheet'),
        ]
    )
