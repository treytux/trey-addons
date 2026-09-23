###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_combination_info(
            self, combination=False, product_id=False, add_qty=1,
            pricelist=False, parent_combination=False, only_template=False):
        product_combination = False
        if combination:
            product_combination = self._get_variant_for_combination(combination)
            if not product_combination:
                combination = self.env['product.template.attribute.value']
        product_id = (
            product_combination or product_id or self.product_variant_id.id)
        combination_info = super()._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty,
            pricelist=pricelist, parent_combination=parent_combination,
            only_template=only_template)
        return combination_info
