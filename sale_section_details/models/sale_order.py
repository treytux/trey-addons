###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    show_section_details = fields.Boolean(
        string='Show section details',
        help='If checked, section details will be shown.',
        default=True,
    )
