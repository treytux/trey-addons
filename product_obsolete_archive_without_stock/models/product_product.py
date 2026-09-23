###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def cron_archive_obsolete_products_without_stock(self):
        products = self.search([
            ('is_obsolete', '=', True),
        ]).filtered(lambda product: product.qty_available <= 0)
        if not products:
            return
        orderpoints = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', 'in', products.ids),
            ('active', '=', True),
        ])
        orderpoints.write({
            'active': False,
        })
        templates = products.mapped('product_tmpl_id')
        products.write({
            'active': False,
        })
        templates.filtered(
            lambda template: not template.product_variant_ids
        ).write({
            'active': False,
        })
