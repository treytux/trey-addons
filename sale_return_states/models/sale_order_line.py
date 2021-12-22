###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    ttype = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('change', 'Change'),
            ('repentance', 'Refund repentances'),
            ('no_stock', 'Refund by no stock'),
            ('repaired', 'Repaired'),
            ('no_default', 'No default'),
            ('out_warranty', 'Out of warranty'),
        ],
        string='State',
        default='draft',
        help='This field is used to select the way to solve the problem of '
             'each line:\n'
             'Draft: Default operations, only return goods to stock.\n'
             'Change: Will create 3 pickings, client to returns location, '
             'from returns to scrap, and new good from stock to client.\n'
             'Refund repentances: Will create 2 pickings, client to returns '
             'and returns to stock.\n'
             'Refund by no stock: Will create 2 pickings, client to returns '
             'and returns to scrap.\n'
             'Repaired/No default/Out of warranty: Will create 2 pickings, '
             'client-returns and returns-client.',
    )
