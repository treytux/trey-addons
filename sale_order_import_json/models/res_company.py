###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    action_msg_price = fields.Selection(
        selection=[
            ('raise_error', 'Raise error'),
            ('post_note', 'Post note'),
        ],
        string='Action checking price in import',
        help='Action when checking price in importer orders',
        default='raise_error',
    )
    skip_commission_agents_zero_value_lines = fields.Boolean(
        string='Skip commission agents on zero value lines',
        help='When enabled, imported sale order lines without economic '
             'value (price_unit_untaxed = 0 or discount = 100) will not '
             'get the partner default commission agents assigned.',
        default=True,
    )
