# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_pack_add(self):
        wiz_obj = self.env['wiz.pack.add']
        wiz_values = {'order_id': self.id}
        wiz = wiz_obj.create(wiz_values)
        context = self.env.context.copy()
        context['default_order_id'] = self.id
        return {
            'name': _('Add pack'),
            'type': 'ir.actions.act_window',
            'res_model': 'wiz.pack.add',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wiz.id,
            'context': context,
            'target': 'new'}
