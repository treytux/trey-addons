###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    contract_lite_supplier_contract_id = fields.Many2one(
        comodel_name='contract_lite_supplier.contract',
        string='Supplier contract',
        ondelete='set null',
    )
