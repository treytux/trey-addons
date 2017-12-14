# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _get_ean_next_code(self, product):
        cat_prefix = (
            product.categ_id.ean_sequence_id and
            product.categ_id.ean_sequence_id.prefix or '')
        com_prefix = (
            product.company_id.ean_sequence_id and
            product.company_id.ean_sequence_id.prefix or '')
        prefix = '%s%s' % (cat_prefix, com_prefix)
        return '%s%s' % (prefix, str(product.id).zfill(12 - len(prefix)))
