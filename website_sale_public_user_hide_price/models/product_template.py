###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hide_shop_price = fields.Boolean(
        default=True,
        string='Hide Shop Price',
        help='Hide product prices on the website shop for public users',
    )

    @api.multi
    def _get_combination_info(
            self, combination=False, product_id=False, add_qty=1,
            pricelist=False, parent_combination=False, only_template=False):
        res = super()._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty,
            pricelist=pricelist, parent_combination=parent_combination,
            only_template=only_template)
        if (self._context.get('force_show_price') or not self.hide_shop_price
                or self.env.user != self.env.ref('base.public_user')):
            return res
        if (self.hide_shop_price
                and self.env.user == self.env.ref('base.public_user')):
            res.update(list_price=0, price=0)
        return res
