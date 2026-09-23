###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import UserError


class SaleOrderMerge(models.TransientModel):
    _name = 'sale.order.merge'
    _description = 'Order Merging Wizard'

    def action_merge(self):
        assert self._context.get('active_ids'), 'Missing active_ids'
        orders = self.env['sale.order'].browse(self._context['active_ids'])
        if len(orders) <= 1:
            raise UserError(_('You must select more than one order'))
        if any(order.state != 'draft' for order in orders):
            raise UserError(_('You must select orders in draft state'))
        partner = orders[0].partner_id
        partner_orders = orders.filtered(lambda o: o.partner_id == partner)
        if len(orders) != len(partner_orders):
            raise UserError(
                _('You can only merge orders from the same customer'))
        partner_invoice = orders[0].partner_invoice_id
        partner_invoice_orders = orders.filtered(
            lambda o: o.partner_invoice_id == partner_invoice)
        if len(orders) != len(partner_invoice_orders):
            raise UserError(
                _('You can only merge orders with the same invoicing address'))
        partner_shipping = orders[0].partner_shipping_id
        partner_shipping_orders = orders.filtered(
            lambda o: o.partner_shipping_id == partner_shipping)
        if len(orders) != len(partner_shipping_orders):
            raise UserError(
                _('You can only merge orders with the same shipping address'))
        pricelist = orders[0].pricelist_id
        pricelist_orders = orders.filtered(
            lambda o: o.pricelist_id == pricelist)
        if len(orders) != len(pricelist_orders):
            raise UserError(
                _('You can only merge orders with the same pricelist'))
        new_order = self.env['sale.order'].create({
            'partner_id': orders[0].partner_id.id,
            'partner_invoice_id': orders[0].partner_invoice_id.id,
            'partner_shipping_id': orders[0].partner_shipping_id.id,
            'pricelist_id': orders[0].pricelist_id.id,
            'origin': ', '.join(filter(None, orders.mapped('origin'))),
            'client_order_ref': ' - '.join(filter(None, list(set(orders.mapped(
                'client_order_ref'))))),
        })
        new_order.message_post_with_view(
            'mail.message_origin_link',
            values={'self': new_order, 'origin': orders},
            subtype_id=self.env.ref('mail.mt_note').id,
        )
        for order in orders:
            order.order_line.write({'order_id': new_order.id})
            order.message_post_with_view(
                'sale_order_merge.message_merged_link',
                values={'self': order, 'destination': new_order},
                subtype_id=self.env.ref('mail.mt_note').id,
            )
        action = self.env.ref('sale.action_quotations')
        res = action.read()[0]
        res.update({
            'res_id': new_order.id,
            'view_type': 'form',
            'view_mode': 'form',
        })
        return res
