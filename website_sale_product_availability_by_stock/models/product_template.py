###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    published_by_stock = fields.Boolean(
        string='Publish if you have stock',
    )

    def get_domain_cron_published_by_stock(self):
        return [('published_by_stock', '=', True)]

    @api.model
    def cron_products_website(self):
        products = self.env['product.template'].search(
            self.get_domain_cron_published_by_stock())
        for product in products:
            product.website_published = product.qty_available_real > 0
