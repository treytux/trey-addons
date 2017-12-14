# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api


class Picking(models.Model):
    _inherit = 'stock.picking'

    invoice_total = fields.Float(
        string='Total',
        compute='compute_invoice_total')

    @api.one
    def compute_invoice_total(self):
        cr, uid, context = self.env.args
        self.invoice_total = 0
        for move in self.move_lines:
            if (move.invoice_state == '2binvoiced' and
                    move.state != 'cancel' and not move.scrapped):
                if move.procurement_id and \
                   move.procurement_id.sudo().sale_line_id:
                    sale_line = move.procurement_id.sudo().sale_line_id
                    if move.product_id.id != sale_line.product_id.id:
                        prices = self.pool['product.pricelist'].price_get(
                            cr, uid,
                            [sale_line.order_id.pricelist_id.id],
                            move.product_id.id, move.product_uom_qty or 1.0,
                            sale_line.order_id.partner_id,
                            context=self.env.context)
                        price_unit = prices[sale_line.order_id.pricelist_id.id]
                    else:
                        price_unit = sale_line.price_unit
                    price_unit = (
                        price_unit * (1 - (sale_line.discount or 0.0) / 100.0))
                    taxes = self.pool.get('account.tax').compute_all(
                        cr, uid, sale_line.tax_id,
                        price_unit, move.product_uos_qty, move.product_id,
                        sale_line.order_id.partner_id)['taxes']
                    self.invoice_total += price_unit * move.product_uos_qty + \
                        sum(t.get('amount', 0.0) for t in taxes)
                else:
                    product = move.product_id.with_context(
                        currency_id=move.company_id.currency_id.id)
                    price_unit = move.product_id.list_price and \
                        move.product_id.list_price or \
                        product.price_get('standard_price')[move.product_id.id]
                    self.invoice_total += price_unit * move.product_uos_qty
