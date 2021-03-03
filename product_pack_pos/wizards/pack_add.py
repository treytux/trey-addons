# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _, exceptions
import logging

_log = logging.getLogger(__name__)


class PackAdd(models.TransientModel):
    _name = 'pos.wiz.pack.add'
    _description = 'Add pack to sale order'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        domain=[('is_pack', '=', True)],
        string='Pack',
        required=False
    )
    quantity = fields.Float(
        string="Quantity", default=1
    )

    @api.one
    def button_add(self):
        # Comprobar que han elegido un producto
        if not self.product_tmpl_id:
            raise exceptions.Warning(
                _('You must introduce a pack.'))

        # Crear una linea para el producto pack
        products = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id)])
        data = {
            'order_id': self._context['active_id'],
            'product_id': products.id,
            'qty': self.quantity,
            'price_unit': products.list_price,
            }
        self.env['pos.order.line'].create(data)

        # Crear una linea por cada producto que tiene el pack

        for pack in self.product_tmpl_id.pack_ids:
            data = {
                'order_id': self._context['active_id'],
                'product_id': pack.product_id.id,
                'qty': pack.quantity * self.quantity,
                'price_unit': 0,
                }
            self.env['pos.order.line'].create(data)

        return {'type': 'ir.actions.act_window_close'}
