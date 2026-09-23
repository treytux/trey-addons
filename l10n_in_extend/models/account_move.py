###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    transport_mode = fields.Char(
        string='Transport Mode',
    )
    vehicle_number = fields.Char(
        string='Vehicle Number',
    )
    supply_date = fields.Char(
        string='Date Supply',
    )
    supply_place = fields.Char(
        string='Place to Supply',
    )
