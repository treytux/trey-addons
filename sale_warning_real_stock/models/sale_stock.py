# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def product_id_change_with_wh(
            self, pricelist, product, qty=0, uom=False, qty_uos=0, uos=False,
            name='', partner_id=False, lang=False, update_tax=True,
            date_order=False, packaging=False, fiscal_position=False,
            flag=False, warehouse_id=False):

        res = super(SaleOrderLine, self).product_id_change_with_wh(
            pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
            name=name, partner_id=partner_id, lang=lang, update_tax=update_tax,
            date_order=date_order, packaging=packaging,
            fiscal_position=fiscal_position, flag=flag,
            warehouse_id=warehouse_id
        )
        product_obj = self.env['product.product']
        warning_msgs = ''
        if product and res['value']['product_uos_qty']:
            product = product_obj.browse(product)
            if res['value']['product_uos_qty'] > product.qty_available:
                warn_msg = \
                    _('You plan to sell %.2f %s but you only have %.2f %s '
                      'available !\nThe real stock is %.2f %s. (without '
                      'reservations)') % \
                    (qty, product.uom_id.name,
                        max(0, product.virtual_available), product.uom_id.name,
                        max(0, product.qty_available), product.uom_id.name)
                warning_msgs += _("Not enough stock ! : ") + warn_msg + "\n\n"

        if warning_msgs:
            warning = {
                'title': _('Configuration Error!'),
                'message': warning_msgs
            }
            res['warning'] = warning
        return res
