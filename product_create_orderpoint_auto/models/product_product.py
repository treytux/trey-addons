###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if not res.orderpoint_ids and res.type != 'service':
            warehouses = self.env.user.company_id.warehouse_auto_orderpoint_ids
            for warehouse in warehouses:
                self.env['stock.warehouse.orderpoint'].create({
                    'name': _('OP/%s') % res.id,
                    'product_id': res.id,
                    'warehouse_id': warehouse.id,
                    'location_id': warehouse.lot_stock_id.id,
                    'product_min_qty': 0,
                    'product_max_qty': 0,
                    'company_id': self.env.user.company_id.id,
                })
        return res
