###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_policy = fields.Selection(
        [('order', 'Ordered quantities'),
         ('delivery', 'Delivered quantities')],
        help='Ordered Quantity: Invoice based on the quantity the customer '
             'ordered.\n'
             'Delivered Quantity: Invoiced based on the quantity the vendor '
             'delivered (time or deliveries).')
