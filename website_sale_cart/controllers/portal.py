###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http, _
from openerp.http import request
try:
    from odoo.addons.portal.controllers.portal import (
        CustomerPortal, pager as portal_pager)
except ImportError:
    CustomerPortal = object


class CustomerPortalCart(CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super(
            CustomerPortalCart, self)._prepare_portal_layout_values()
        partner_id = request.env.user.partner_id.commercial_partner_id.id
        values['cart_count'] = request.env['sale.order'].sudo().search_count([
            ('partner_id', 'child_of', [partner_id]),
            ('state', 'in', ['draft'])])
        return values

    @http.route(
        ['/my/carts', '/my/carts/page/<int:page>'],
        type='http', auth='user', website=True)
    def portal_my_carts(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        partner_id = request.env.user.partner_id.commercial_partner_id.id
        domain = [
            ('partner_id', 'child_of', [partner_id]),
            ('state', 'in', ['draft'])]
        archive_groups = self._get_archive_groups('sale.order', domain)
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end)]
        sale_order = request.env['sale.order'].sudo()
        quotation_count = sale_order.search_count(domain)
        sortby = sortby or 'date'
        pager = portal_pager(
            url='/my/carts',
            url_args={
                'date_begin': date_begin, 'date_end': date_end,
                'sortby': sortby},
            total=quotation_count,
            page=page,
            step=self._items_per_page)
        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'date_order desc'}}
        carts = sale_order.search(
            domain, order=searchbar_sortings[sortby]['order'],
            limit=self._items_per_page, offset=pager['offset'])
        request.session['my_carts_history'] = carts.ids[:100]
        values = self._prepare_portal_layout_values()
        values.update({
            'date': date_begin,
            'carts': carts.sudo(),
            'page_name': 'cart',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/carts',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby})
        return request.render('website_sale_cart.portal_my_carts', values)

    def _cart_check_access(self, cart_id):
        partner_id = request.env.user.partner_id.commercial_partner_id.id
        order_sudo = request.env['sale.order'].sudo().search([
            ('id', '=', cart_id),
            ('partner_id', 'child_of', [partner_id]),
            ('state', 'in', ['draft'])])
        return order_sudo

    @http.route([
        '/my/cart/recover/<int:cart>',
    ], type='http', auth='user', website=True)
    def portal_cart_recover(self, cart):
        cart_sudo = self._cart_check_access(cart)
        if not cart_sudo:
            return request.redirect('/my')
        request.session['sale_order_id'] = cart_sudo.id
        return request.redirect('/shop/cart')
