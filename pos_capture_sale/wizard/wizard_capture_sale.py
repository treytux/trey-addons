# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _


class WizPosCaptureSale(models.TransientModel):
    _name = 'wiz.pos.capture.sale'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True)

    @api.multi
    def button_pos_capture_sale(self):

        # Crear un pedido TPV
        data_pos = {
            'partner_id': self.order_id.partner_id and
            self.order_id.partner_id.id or None,
            'pricelist_id': self.order_id.pricelist_id and
            self.order_id.pricelist_id.id or None,
            'sale_order_id': self.order_id.id
        }
        pos = self.env['pos.order'].create(data_pos)

        for line in self.order_id.order_line:
            data_line = {
                'order_id': pos.id,
                'product_id': line.product_id.id,
                'qty': line.product_uom_qty,
                'price_unit': line.price_unit,
                'discount': line.discount,
                }
            self.env['pos.order.line'].create(data_line)

        # Cambiar el estado del pedido de venta y relacionarlo con el pedido
        # TPV
        sale_order = self.env['sale.order'].browse(self.order_id.id)
        sale_order.write({
            'state': 'manage_from_pos',
            'pos_order_id': pos.id
        })

        # Abrir el pedido TPV creado
        return {
            'name': _('PoS order'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': pos.id
        }
