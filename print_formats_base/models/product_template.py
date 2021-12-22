###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    add_to_sum_qty = fields.Boolean(
        string='Include in print formats line summation',
        help="If you check this box this product will be consider to make the "
        "quantity sums in the print formats. This sum is an informative value "
        "for the operation of the business.",
        default=True,
    )
