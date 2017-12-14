# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Delivery method')

    @api.multi
    def onchange_partner_id(self, partner_id):
        '''Assign the carrier defined in the partner.'''
        result = super(PurchaseOrder, self).onchange_partner_id(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            result['value']['carrier_id'] = (
                partner.property_delivery_carrier and
                partner.property_delivery_carrier.id or None)
        return result

    @api.multi
    def action_picking_create(self):
        '''When the picking in is created, the carrier is assigned.'''
        picking_id = super(PurchaseOrder, self).action_picking_create()
        picking = self.env['stock.picking'].browse(picking_id)
        picking.write(
            {'carrier_id': self.carrier_id and self.carrier_id.id or None})
        return picking_id
