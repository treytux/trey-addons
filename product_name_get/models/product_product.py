###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def name_get(self):
        pattern = self.env['ir.config_parameter'].sudo().get_param(
            'product_name_get.product_product_name_pattern')
        if not pattern or 'partner_id' in self._context:
            return super().name_get()
        parser = self[0].product_tmpl_id._name_get_parse
        return [(p.id, parser(pattern, p)) for p in self]
