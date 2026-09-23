###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get('check_auto_creation'):
            return super().create(vals_list)
        for count, vals in enumerate(vals_list):
            product_tmpl_id = vals.get('product_tmpl_id')
            if not product_tmpl_id:
                continue
            product_tmpl = self.env['product.template'].browse(product_tmpl_id)
            if product_tmpl.categ_id.disable_supplierinfo_creation:
                vals_list.pop(count)
        return super().create(vals_list)
