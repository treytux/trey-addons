###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    contract_lite_supplier_line_id = fields.Many2one(
        comodel_name='contract_lite_supplier.line',
        string='Supplier contract line',
        ondelete='set null',
        help='Supplier contract line linked to this vendor bill line.',
    )
