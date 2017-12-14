# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
from openerp.http import request
from openerp.addons.website_sale.controllers.main import website_sale


class WebsiteSale(website_sale):
    @http.route()
    def checkout(self, **post):
        env = request.env
        website = request.website
        partner_obj = env['res.partner']
        user = env['res.users'].sudo().browse(request.uid)
        if request.uid != website.user_id.id and user.partner_id.agent:
            values = self.checkout_values()
            domain = [('agents', 'in', [user.partner_id.id])]
            partners = partner_obj.sudo().search(domain, order='name asc')
            values['partners'] = partners
            return website.render(
                'website_sale_checkout_agent.checkout_agent', values)
        return super(WebsiteSale, self).checkout(**post)

    @http.route(['/shop/agent_confirm'], type='http', auth="user",
                website=True, multilang=True)
    def confirm_agent_order(self, **post):
        if not post:
            return request.redirect('/shop')
        env = request.env
        website = request.website
        order_obj = env['sale.order']
        order = website.sale_get_order()
        if not order:
            order = order_obj.sudo().browse(
                int(request.session.get('sale_last_order_id')))
            if not order:
                return request.redirect('/shop')
            return website.render(
                'website_sale_checkout_agent.agent_confirm', {'order': order})
        order_info = {}
        if post.get('partner_id') != 'new-customer':
            partner = env['res.partner'].sudo().browse(
                int(post.get('partner_id')))
            order_info.update({
                'partner_id': partner.id,
                'fiscal_position': partner.property_account_position.id,
                'message_follower_ids': [(4, partner.id),
                                         (3, request.website.partner_id.id)],
                'partner_shipping_id': (int(post.get('partner_shipping_id'))),
                'partner_invoice_id': (int(post.get('partner_invoice_id')))})
            order_info.update(
                order.sudo().onchange_partner_id(partner.id)['value'])
        else:
            partner = order.partner_id.root_partner_id
            order_info.update({'partner_id': partner.id})
            order_info.update(
                order.sudo().onchange_partner_id(partner.id)['value'])
        fiscal_update = order.sudo().onchange_fiscal_position(
            partner.property_account_position.id, [
                (4, l.id) for l in order.order_line])['value']
        order_info.update(fiscal_update)
        transaction_obj = env['payment.transaction']
        note = post.get('note')
        order_info.update({'note': note})
        order.sudo().write(order_info)
        season = None
        order.recalculate_prices()
        for line in order.order_line:
            season = line.product_id.season_id
        request.session['sale_last_order_id'] = order.id
        acquired = env.ref(
            'payment_direct_order.payment_acquirer_direct_order')
        tx = transaction_obj.sudo().create({
            'acquirer_id': acquired.id,
            'type': 'form',
            'amount': order.amount_total,
            'currency_id': order.pricelist_id.currency_id.id,
            'partner_id': order.partner_id.id,
            'partner_country_id': order.partner_id.country_id.id,
            'reference': transaction_obj.get_next_reference(order.name),
            'sale_order_id': order.id,
            'state': 'pending'})
        request.session['sale_transaction_id'] = tx
        request.session['sale_last_order_id'] = order.id
        order.sudo().write({
            'payment_acquirer_id': acquired.id,
            'payment_tx_id': tx.id,
            'season_id': season and season.id or None})
        order.sudo().force_quotation_send()
        website.sale_reset()
        return website.render(
            'website_sale_checkout_agent.agent_confirm', {'order': order})
