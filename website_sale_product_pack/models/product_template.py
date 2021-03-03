###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def _get_combination_info(
            self, combination=False, product_id=False, add_qty=1,
            pricelist=False, parent_combination=False, only_template=False):
        self.ensure_one()
        only_template = (
            only_template if not self.pack_ok
            or self.product_variant_count != 1 else False
        )
        return super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id,
            add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template,
        )
