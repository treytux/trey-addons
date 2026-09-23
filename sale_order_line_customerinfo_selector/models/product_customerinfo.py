###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductCustomerInfo(models.Model):
    _inherit = 'product.customerinfo'

    def name_get(self):
        result = []
        for customerinfo in self:
            name = (
                customerinfo.product_name or customerinfo.product_code
                or customerinfo.partner_id.display_name)
            result.append((customerinfo.id, name))
        return result
