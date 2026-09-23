###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    stock_field = fields.Selection(
        selection=[
            ('virtual_available', 'Virtual Available'),
            ('qty_available', 'Quantity Available'),
        ],
        string='Stock Field',
        default='qty_available',
    )
