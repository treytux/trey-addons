###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('discount')
    def _check_discount(self):
        for line in self:
            if line.discount < 0.0 or line.discount > 100.0:
                raise exceptions.ValidationError(_(
                    'Discount must be between 0 and 100.'))
