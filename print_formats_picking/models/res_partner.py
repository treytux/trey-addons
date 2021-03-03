###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    delivery_slip_type = fields.Selection(
        selection=[
            ('valued', 'Valued'),
            ('not_valued', 'Not valued')
        ],
        string='Delivery slip type',
        required=True,
        default='valued',
        help='Set type of delivery slip for this partner',
    )
