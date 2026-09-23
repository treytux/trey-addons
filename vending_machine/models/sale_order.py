###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    machine_ids = fields.Many2many(
        comodel_name='vending.machine',
        string='Vending Machines',
        help='The vending machines where the order will be processed.',
        readonly=True,
    )
    date_stock_deposit = fields.Date(
        string='Date Stock Deposit',
        help='The date of the stock deposit.',
        readonly=True,
    )
