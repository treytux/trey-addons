# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.multi
    def _compute_unit_price(self):
        super(ProductSupplierInfo, self)._compute_unit_price()
        for supplierinfo in self:
            if len(supplierinfo.pricelist_ids) == 0:
                supplierinfo.unit_price_note = '-'
            else:
                txt = ''
                size = len(supplierinfo.pricelist_ids)
                uom_precision = supplierinfo.product_tmpl_id.uom_id.rounding
                pricelists = supplierinfo.pricelist_ids
                for i in range(size - 1):
                    current_pl = pricelists[i]
                    next_pl = pricelists[i + 1]
                    txt += '%s - %s :  %s\n' % (
                        current_pl.min_quantity,
                        (next_pl.min_quantity - uom_precision),
                        current_pl.price * (
                            1 - (current_pl.discount or 0.0) / 100.0))
                txt += '>=%s : %s' % (
                    pricelists[size - 1].min_quantity,
                    pricelists[size - 1].price * (
                        1 - (pricelists[size - 1].discount or 0.0) / 100.0))
                supplierinfo.unit_price_note = txt
