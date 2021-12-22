###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class WizProductLabelFromPickingLine(models.TransientModel):
    _inherit = 'product.label.line'

    product_customer_code = fields.Char(
        string='Product Customer Code',
    )
