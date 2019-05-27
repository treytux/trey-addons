# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrderImport(models.TransientModel):
    _inherit = 'sale.order.import'

    @api.model
    def parse_csv_order(self, order_file, partner):
        parsed_order = super(SaleOrderImport, self).parse_csv_order(
            order_file, partner)
        if not parsed_order.get('currency', False):
            parsed_order['currency'] = {
                'recordset': (
                    partner.property_product_pricelist and
                    partner.property_product_pricelist.currency_id or None)}
        return parsed_order
