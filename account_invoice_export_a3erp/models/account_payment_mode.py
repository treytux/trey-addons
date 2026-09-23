###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountPaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    operation_type_a3erp = fields.Char(
        string='Operation type for export to a3ERP format',
        size=4,
    )
    tax_type_a3erp = fields.Char(
        string='Tax type for export to a3ERP format',
        size=4,
    )
