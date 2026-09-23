###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    notification_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Warehouse by condition notification user',
        help=(
            'User to be notified of errors when condition lines are applied '
            'for the  condition procurement group warehouse.\n'
            'If left empty, the sales order\'s salesperson will be notified, '
            'and if there is no salesperson associated, the user who '
            'confirmed the order.'
        ),
    )
    product_qty_field = fields.Selection(
        selection=[
            ('qty_available', 'Qty on hand'),
            ('virtual_available', 'Forecasted quantity'),
        ],
        string='Product quantity field',
        help='Select how you want to calculate the quantity when the '
             'warehouse performs the stock check based on conditions.',
        default='qty_available',
        required=True,
        ondelete='set default',
    )
