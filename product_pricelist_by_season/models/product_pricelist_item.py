###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    applied_on = fields.Selection(
        selection_add=[('1_season', 'Season')],
        ondelete={'1_season': 'set default'},
    )
    product_season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season',
    )

    @api.depends('applied_on', 'categ_id', 'product_tmpl_id', 'product_id',
                 'compute_price', 'fixed_price', 'pricelist_id',
                 'percent_price', 'price_discount', 'price_surcharge',
                 'product_season_id')
    def _compute_name_and_price(self):
        super()._compute_name_and_price()
        for item in self:
            if item.applied_on == '1_season' and item.product_season_id:
                item.name = _("Season: %s") % (item.product_season_id.name)
            if item.applied_on != '1_season':
                item.product_season_id = False

    def _is_applicable_for(self, product, qty_in_product_uom):
        is_applicable = super()._is_applicable_for(product, qty_in_product_uom)
        if not is_applicable:
            return is_applicable
        if self.product_season_id:
            if product.season_id != self.product_season_id:
                return False
        return is_applicable
