# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.


from openerp import models, api


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.model
    def _get_mts_mto_procurement(self, proc, rule, qty, uos_qty):
        res = super(ProcurementOrder, self)._get_mts_mto_procurement(
            proc=proc, rule=rule, qty=qty, uos_qty=qty)
        res['name'] = proc.name
        return res

    @api.model
    def _assign(self, procurement):
        stock_loc = self.env.ref('stock.stock_location_stock')
        if procurement.location_id == stock_loc:
            procurement.origin = ''
        res = super(ProcurementOrder, self)._assign(procurement)
        return res
