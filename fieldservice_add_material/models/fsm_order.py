###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class FsmOrder(models.Model):
    _inherit = 'fsm.order'

    stage_is_closed = fields.Boolean(
        related='stage_id.is_closed',
    )
    base_stock_already_delivered = fields.Boolean(
        string='Base stock already delivered',
        help='''Will be activated when fieldservice order base stock is
                delivered partially or totally.''',
    )
