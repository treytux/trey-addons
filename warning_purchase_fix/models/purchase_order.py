# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def onchange_partner_id(self, partner_id):
        res = super(PurchaseOrder, self).onchange_partner_id(partner_id)
        res.setdefault('value', {})
        if 'fiscal_postion' not in res['value']:
            partner = self.env['res.partner'].browse(partner_id)
            res['value']['fiscal_position'] = (
                partner.property_account_position and
                partner.property_account_position.id or None)
        return res
