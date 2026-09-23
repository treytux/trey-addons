###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_website_sale_stock_website(self):
        website = self.env['website'].browse(
            self.env.context.get('website_id')).exists()
        if website:
            return website
        try:
            return self.env['website'].get_current_website()
        except RuntimeError:
            return self.env['website']

    def _get_combination_info(
            self, combination=False, product_id=False, add_qty=1,
            pricelist=False, parent_combination=False, only_template=False):
        website = self._get_website_sale_stock_website()
        template = self
        mode = website and website._get_website_sale_stock_qty_mode()
        if mode and mode != 'available':
            template = template.with_context(
                website_sale_stock_qty_mode=mode)
        return super(ProductTemplate, template)._get_combination_info(
            combination, product_id, add_qty, pricelist, parent_combination,
            only_template)
