###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    applied_on = fields.Selection(
        selection_add=[('3_season', 'Season')],
    )
    product_season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season',
    )

    @api.onchange('applied_on')
    def _onchange_applied_on(self):
        res = super()._onchange_applied_on()
        if self.applied_on != '3_season':
            self.product_brand_id = False
        return res

    @api.depends('categ_id', 'product_tmpl_id', 'product_id', 'compute_price',
                 'fixed_price', 'pricelist_id', 'percent_price',
                 'price_discount', 'price_surcharge', 'product_brand_id')
    def _get_pricelist_item_name_price(self):
        res = super()._get_pricelist_item_name_price()
        for item in self:
            if item.product_season_id:
                item.name = _('Season: %s') % item.product_season_id.name
        return res
