###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class WizProductLabel(models.TransientModel):
    _inherit = 'product.label'

    def get_line_values(self, move_rec, qty, qty_use):
        res = super().get_line_values(move_rec, qty, qty_use)
        res['product_customer_code'] = move_rec.product_customer_code
        return res
