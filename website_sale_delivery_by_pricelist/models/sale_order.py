# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
###############################################################################
from openerp import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_delivery_domain(self, res_ids, order):
        pricelist_ids = list(set(
            order.partner_id.property_product_pricelist.ids +
            order.pricelist_id.ids
        ))
        return [
            ('id', 'in', res_ids),
            ('pricelist_id', 'in', pricelist_ids),
        ]

    @api.model
    def _get_delivery_methods(self, order):
        res_ids = super(SaleOrder, self)._get_delivery_methods(order)
        delivery_objs = self.env['delivery.carrier'].search(
            self._get_delivery_domain(res_ids, order))
        return delivery_objs and delivery_objs.ids or []
