###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    last_instore_txn_id = fields.Char(
        string='InStore transaction ID',
    )
    last_instore_tx_number = fields.Char(
        string='InStore transaction number',
    )
    instore_device_id = fields.Char(
        string='InStore device ID',
    )
    instore_device_tx_status = fields.Char(
        string='InStore device transaction status',
    )
