# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.##
from openerp import models, api, _
import logging
_log = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        # Actualizar el precio medio variable de los articulos en base al
        # precio de factura teniendo en cuenta el stock actual.
        if self.type == 'in_invoice':
            product_template_obj = self.env['product.template']
            for line in self.invoice_line:
                # TODO: ver que hacemos si el precio medio variable es 0
                if line.product_id.product_tmpl_id.type == 'product':
                    old_qty = line.product_id.product_tmpl_id.qty_available
                    old_price = line.product_id.product_tmpl_id.standard_price
                    new_qty = line.quantity
                    new_price = line.price_subtotal / line.quantity
                    if new_qty <= 0:
                        continue
                    if old_qty <= 0:
                        old_qty = 0
                        _log.warn(_(
                            'The product "%s" Id %s has out of stock, '
                            'please ajust inventory and try again.' % (
                                line.product_id.product_tmpl_id.name,
                                line.product_id.product_tmpl_id.id)))
                    middle_price = (
                        (old_price * old_qty) + (new_price * new_qty))
                    middle_price = (
                        middle_price / (old_qty + new_qty))
                    template = product_template_obj.browse(
                        line.product_id.product_tmpl_id.id)
                    template.write({'standard_price': middle_price})
        super(AccountInvoice, self).invoice_validate()
