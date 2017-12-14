# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2014-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
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
