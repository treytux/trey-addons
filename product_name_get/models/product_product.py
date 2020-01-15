###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import models, api
import logging
_log = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def find_possible_fields(self, name_pattern):
        begin = '%('
        end = ')s'
        fields = []
        for subs in name_pattern.split(begin):
            if not subs or subs.find(end) == -1:
                continue
            subs_parts = subs.split(end)
            fields.append(subs_parts[0])
        return fields

    @api.multi
    def name_get(self):
        result = []
        name_pattern = self.env['ir.config_parameter'].sudo().get_param(
            'product_name_get.product_product_name_pattern', default='')
        origin = super(ProductProduct, self).name_get()
        data = {}
        for product in self:
            possible_fields = self.find_possible_fields(name_pattern)
            for poss_field in possible_fields:
                if poss_field not in product._fields:
                    _log.error((
                        '[name_get product.product]: the field \'%s\' does '
                        'not found in model.' % poss_field))
                    return origin
                data.update({
                    poss_field: getattr(product, poss_field) or '',
                })
            name = name_pattern % data
            result.append((product.id, name))
        return result
