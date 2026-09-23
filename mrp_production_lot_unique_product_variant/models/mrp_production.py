###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.one
    @api.constrains('name', 'product_id')
    def check_name_unique_product_variants(self):
        for product in self.product_id.product_tmpl_id.product_variant_ids:
            all_lots = []
            for variant in product.product_tmpl_id.product_variant_ids:
                lots = self.env['stock.production.lot'].search([
                    ('product_id', '=', variant.id),
                    ('name', '=', self.name),
                ])
                variant_lots = lots.mapped('name')
                all_lots += variant_lots
                if len(all_lots) > 1:
                    raise ValidationError(
                        _('The serial number "%s" is already in use in another'
                          ' variant of this product.') % self.name)
