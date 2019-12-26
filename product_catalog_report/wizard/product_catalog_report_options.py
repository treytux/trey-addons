###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductCatalogReport(models.TransientModel):
    _name = 'product.catalog.report_options'
    _description = 'Print options product catalog'
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        default=1,
        required=1,
        string='Pricelist')

    @api.multi
    def button_print(self, data):
        self.ensure_one()
        prod_cat_rep = 'product_catalog_report.report_product_catalog_create'
        data['pricelist_id'] = self.pricelist_id.id
        return self.env.ref(prod_cat_rep).report_action(self, data)
