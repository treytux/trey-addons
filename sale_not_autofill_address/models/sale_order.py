# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def onchange_partner_id(self, partner_id):
        res = super(SaleOrder, self).onchange_partner_id(partner_id)
        partner = self.env['res.partner'].browse(partner_id)
        has_shippings = [True for child in partner.child_ids
                         if child.type == 'delivery']
        has_invoice_addresses = [True for child in partner.child_ids
                                 if child.type == 'invoice']
        if len(partner.child_ids.ids) > 1:
            if has_shippings and res['value']['partner_shipping_id']:
                res['value']['partner_shipping_id'] = None
            if has_invoice_addresses and res['value']['partner_invoice_id']:
                res['value']['partner_invoice_id'] = None
        return res
