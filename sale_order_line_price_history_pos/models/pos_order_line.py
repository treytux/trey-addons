###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    state = fields.Selection(
        related='order_id.state',
    )
    order_partner_id = fields.Many2one(
        related='order_id.partner_id',
    )
