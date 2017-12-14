# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def action_open_procurement(self):
        for line in self:
            procurement_lst = []
            for procurement in line.procurement_ids:
                procurement_lst.append(procurement.id)
        return {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'procurement.order',
            'res_ids': procurement_lst,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', procurement_lst)]}
