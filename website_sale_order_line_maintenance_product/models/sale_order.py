###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def enable_maintenance(self):
        for sale in self:
            lines = sale.order_line.filtered(
                lambda ln: not ln.is_maintenance_line and not
                ln.is_maintenance_section
                and ln.product_id.product_tmpl_id.maintenance_percentage)
            lines.write({
                'is_not_increases_maintenance_price': False,
            })
            return True

    def disable_maintenance(self):
        for sale in self:
            lines = sale.order_line.filtered(
                lambda ln: not ln.is_maintenance_line and not
                ln.is_maintenance_section)
            lines.write({
                'is_not_increases_maintenance_price': True,
            })
            return True
