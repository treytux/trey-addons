###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    contract_lite_line_id = fields.Many2one(
        comodel_name='contract_lite.line',
        string='Contract line',
        index=True,
        ondelete='set null',
        help='Contract line associated to this invoice line.',
    )
