###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _search_get_detail(self, website, order, options):
        res = super()._search_get_detail(website, order, options)
        domain = res['base_domain']
        categ_id = options.get('product_category')
        if categ_id:
            domain.append([('categ_id', '=', categ_id)])
        res['base_domain'] = domain
        return res
