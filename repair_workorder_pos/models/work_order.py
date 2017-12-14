# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _


class WorkOrder(models.Model):
    _inherit = 'repair.workorder'

    pos_id = fields.Many2one(
        comodel_name='pos.order',
        string='POS Order')

    @api.multi
    def action_create_pos_order(self):
        wo = self[0]
        if not wo.pos_id:
            order = self.env['pos.order'].create({
                'workorder_id': wo.id,
                'partner_id': wo.partner_id.id,
            })
            for line in wo.consumed_ids:
                self.env['pos.order.line'].create({
                    'order_id': order.id,
                    'product_id': line.product_id.id,
                    'qty': line.quantity,
                    'price_unit': line.price_unit
                })
            self.pos_id = order.id

        res = self.env['ir.model.data'].get_object_reference(
            'point_of_sale', 'view_pos_pos_form')
        res_id = res and res[1] or False
        return {
            'name': _('Create POS order'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'pos.order',
            'res_id': wo.id,
            # 'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }
